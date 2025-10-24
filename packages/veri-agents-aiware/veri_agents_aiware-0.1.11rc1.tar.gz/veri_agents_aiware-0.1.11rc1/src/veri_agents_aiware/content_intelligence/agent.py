import json
import logging
from datetime import datetime
from typing import Annotated, Any, List, Optional, Sequence, TypedDict, cast

from aiware.client import AsyncAiware
from langchain_core.messages import SystemMessage, HumanMessage
from veri_agents_aiware.content_intelligence.data import format_table_delimited
from langchain_core.language_models import LanguageModelLike
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, ToolMessage
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer
from pydantic import BaseModel, Field
from veri_agents_aiware.aiware_client.async_client import AsyncAgentsAiware
from veri_agents_aiware.content_intelligence.adapters import AiwareSegmentAdapter
from veri_agents_aiware.content_intelligence.data import TargetSelector
from veri_agents_aiware.content_intelligence.executor import Executor
from veri_agents_aiware.content_intelligence.executor import State as ExecutorState
from veri_agents_aiware.content_intelligence.plan import (
    CreatePlanTool,
    InvalidPlanError,
    Plan,
)
from veri_agents_aiware.content_intelligence.prompts import (
    get_system_prompt,
    get_summary_prompt,
    get_chunk_summary_prompt,
    get_aggregate_summaries_prompt,
)

log = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    query: str | None
    plan: Plan | None
    executor_result: dict[str, Any] | None
    plan_validation_errors: list[str] | None
    # For bulk processing
    context_chunks: list[str] | None
    chunk_summaries: list[str] | None
    current_chunk: str | None  # For individual chunk processing
    chunk_index: int | None  # For tracking chunk order


def estimate_tokens(text: str, model_name: str = "gpt-4") -> int:
    """Estimate the number of tokens in a text string using LangChain's approximation.

    Args:
        text: The text to count tokens for
        model_name: The model name (not used but kept for compatibility)

    Returns:
        Estimated number of tokens
    """
    return count_tokens_approximately([text])


def format_structured_table_for_context(table_data: dict) -> str:
    """Format structured table data for LLM context."""
    alias = table_data.get("alias", "unknown")
    status = table_data.get("status", "unknown")
    shape = table_data.get("shape", (0, 0))

    if status == "missing":
        return f"{alias}: Table not found"
    elif status == "empty":
        return f"{alias}: Table is empty"
    elif status != "ok":
        return f"{alias}: Table status: {status}"

    # Get the actual polars DataFrame
    df = table_data.get("data")
    if df is None:
        return f"{alias}: No data available"

    formatted_table = format_table_delimited(
        df,
        delimiter="\t",
        text_preview=None,
        round_digits=4,
        add_footer=True,
        limit_rows=10000,  # Large limit for now, we'll handle chunking separately
    )

    return f"{alias} ({shape[0]} rows, {shape[1]} cols):\n{formatted_table}"


def chunk_text_tables(
    formatted_tables: list[str], max_tokens_per_chunk: int = 50000
) -> list[str]:
    """
    Split pre-formatted table strings into manageable chunks for bulk processing.

    Args:
        formatted_tables: List of already formatted table strings
        max_tokens_per_chunk: Maximum tokens per chunk

    Returns:
        List of text chunks, each containing one or more tables
    """
    chunks = []
    current_chunk = ""
    current_tokens = 0

    for table_text in formatted_tables:
        table_tokens = estimate_tokens(table_text)

        # If adding this table would exceed the limit, save current chunk and start new one
        if current_tokens + table_tokens > max_tokens_per_chunk and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = table_text
            current_tokens = table_tokens
        else:
            # Add table to current chunk
            if current_chunk:
                current_chunk += "\n\n" + table_text
            else:
                current_chunk = table_text
            current_tokens += table_tokens

    # Add the last chunk if it has content
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


class ContentIntelligenceInput(BaseModel):
    """Input schema for the content intelligence agent

    Has to be passed in the Runtime context.
    For example:
    ```
    graph.invoke(
        {"messages": [HumanMessage("What's the screen time for John?")]},
        context={
            "target": {"kind": "tdo_ids", "tdo_ids": ["tdo1", "tdo2"]}}
            "aiware_client": ...
        }
    )
    ```
    """

    # perhaps default to everything in the org?
    target: TargetSelector = Field(
        description="Selector for target media (by folder or list of TDO IDs)"
    )

    # aiware_auth: AbstractAiwareToken | str = Field(
    #    description="Authentication token or AbstractAiwareToken instance for aiWARE access"
    # )
    # TODO: for now we pass this in the function call, means you have to recreate the graph if it changes
    # aiware_client: AsyncAgentsAiware


def create_content_intelligence_agent(
    model: LanguageModelLike,
    aiware_client: AsyncAiware,
    model_bulk: LanguageModelLike | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    interrupt_before: list[str] | None = None,
    interrupt_after: list[str] | None = None,
    debug: bool = False,
    name: str | None = None,
    max_tokens_per_request: int = 80000,
    **kwargs,
) -> CompiledStateGraph[AgentState, ContentIntelligenceInput, AgentState, AgentState]:
    """Create a content intelligence agent workflow for media analysis queries.

    The agent uses an LLM to create an execution plan, executes it against aiWARE, and summarizes the results.

    Args:
        model: Language model to use for planning and summarization.
        aiware_client: Initialized AsyncAgentsAiware client for aiWARE access.
        model_bulk: Optional language model for bulk operations on large contexts (>100k tokens).
                   If not provided, the main model will be used for all operations.
        checkpointer: Optional checkpointer for workflow state.
        store: Optional store for persisting workflow state.
        interrupt_before: Optional list of node names to interrupt before execution.
        interrupt_after: Optional list of node names to interrupt after execution.
        debug: Whether to enable debug mode.
        name: Optional name for the workflow.

    Returns:
        CompiledStateGraph: The compiled workflow LangGraph graph.
    """
    aiware_client = AsyncAgentsAiware.extend_async(aiware_client)
    plan_tool = CreatePlanTool()
    tools = [plan_tool]
    tool_node = ToolNode(tools)
    model_with_tools = cast(BaseChatModel, model).bind_tools(tools)

    async def prepare_plan(state: AgentState):
        """Use LLM with tools to create an execution plan."""
        messages = state["messages"]

        # Extract the query from the last human message
        query: Optional[str] = None
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "human":
                content = msg.content
                if isinstance(content, str):
                    query = content
                    break

        if not query:
            query = state.get("query") or ""

        log.info(f"Preparing plan for query: {query}")

        try:
            # Prepare messages with system prompt

            # Add system prompt if not already present
            system_present = any(
                hasattr(msg, "type") and msg.type == "system" for msg in messages
            )
            if not system_present:
                messages_with_system = [
                    SystemMessage(content=get_system_prompt(str(datetime.now().date())))
                ] + list(messages)
            else:
                messages_with_system = list(messages)

            # Call LLM with tools to create a plan
            response = await model_with_tools.ainvoke(messages_with_system)

            # when preparing a new plan, we want a new clean state
            return {
                "messages": [response],
                "query": query,
                "plan": None,
                "executor": None,
                "plan_validation_errors": None,
                "context_chunks": None,
                "chunk_summaries": None,
                "current_chunk": None,
                "chunk_index": None,
            }

        except Exception as e:
            log.error(f"Failed to prepare plan: {e}")
            return {
                "query": query,
                "plan": None,
                "plan_validation_errors": [str(e)],
            }

    async def process_plan(state: AgentState):
        """Process the tool call results to extract the plan."""
        messages = state["messages"]

        # Find the last tool message
        plan = None
        reasoning = ""
        validation_errors = []

        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "tool":
                try:
                    tool_msg = cast(ToolMessage, msg)
                    if tool_msg.artifact and tool_msg.artifact.get("success"):
                        plan = Plan.model_validate(tool_msg.artifact.get("plan"))
                        reasoning = tool_msg.artifact.get("reasoning", "")
                        log.info(f"Plan extracted from tool result: {len(plan.steps)} steps")
                        break
                    else:
                        validation_errors.append(
                            f"Tool failed: {tool_msg.artifact.get('error')}"
                        )
                except Exception as e:
                    validation_errors.append(f"Failed to parse tool result: {str(e)}")

        if plan is None and not validation_errors:
            validation_errors.append("No plan was created by the LLM")

        #message = f"Executing plan:\n\n{str(plan.prettify()) if plan else 'No valid plan'}.\n\nReasoning: {reasoning if reasoning else 'N/A'}."

        return {
            #"messages": [AIMessage(content=message)],
            "plan": plan,
            "plan_validation_errors": validation_errors,
        }

    async def should_call_tools(state: AgentState) -> str:
        """Decide if we should call tools or answer without making a plan."""
        messages = state["messages"]

        # Check if the last message has tool calls
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "tool_calls") and getattr(
                last_msg, "tool_calls", None
            ):
                return "tools"

        return "done"

    async def verify_plan(state: AgentState):
        """Verify the generated plan is valid."""
        plan = state.get("plan")
        errors = []

        if plan is None:
            errors.append("No plan was generated")
        else:
            try:
                # Validate the plan structure
                Plan.model_validate(plan.model_dump(by_alias=True))
                log.info("Plan validation successful")
            except Exception as e:
                errors.append(f"Plan validation failed: {str(e)}")
                log.error(f"Plan validation error: {e}")

        return {
            "plan_validation_errors": errors,
        }

    async def execute_plan(
        state: AgentState, runtime: Runtime[ContentIntelligenceInput]
    ):
        """Execute the validated plan using the Executor."""
        target = runtime.context.target
        plan = state.get("plan")
        query = state.get("query") or ""

        if plan is None:
            error_msg = "Cannot execute: No valid plan available"
            log.error(error_msg)
            return {
                "messages": [AIMessage(content=error_msg)],
            }

        try:
            log.info(f"Executing plan with {len(plan.steps)} steps")

            # Create executor state and run
            executor_state = ExecutorState(target=target, query=query, plan=plan)

            segment_adapter = AiwareSegmentAdapter(aiware_client)
            executor = Executor(segment_adapter=segment_adapter)
            result_state = await executor.run(executor_state)

            log.info("Plan execution completed successfully")

            # Convert DataFrames to serializable format immediately
            executor_result = result_state.answer
            if executor_result and "summary" in executor_result:
                # Convert structured data to text format for agent state
                summary_data = executor_result["summary"]
                formatted_tables = []
                for table_data in summary_data:
                    formatted_table = format_structured_table_for_context(table_data)
                    formatted_tables.append(formatted_table)

                # Store formatted text instead of DataFrames
                serializable_result = {
                    "summary_text": formatted_tables,
                    "summary_formatted": executor_result.get("summary_formatted", []),
                }

                return {"executor_result": serializable_result}

            return {"executor_result": executor_result}
        except InvalidPlanError as ipe:
            # TODO: in this case replan n times
            error_msg = f"Plan execution failed due to invalid plan: {str(ipe)}"
            log.error(error_msg)
            return {
                "messages": [AIMessage(content=error_msg)],
            }

        except Exception as e:
            error_msg = f"Plan execution failed: {str(e)}"
            log.error(error_msg)
            return {
                "messages": [AIMessage(content=error_msg)],
            }

    async def summarize(state: AgentState):
        """Use LLM to generate a final answer based on execution results."""
        query = state.get("query", "") or ""
        executor_result = state.get("executor_result")

        if not executor_result:
            error_msg = "Cannot summarize: No execution results available"
            log.error(error_msg)
            return {
                "messages": [AIMessage(content=error_msg)],
            }

        try:
            # Prepare context for the LLM
            context_parts = []
            context_parts.append(f"Original Query: {query}")

            # Get formatted table text from executor
            summary_tables = executor_result.get("summary_text", [])

            if not summary_tables:
                context_parts.append("Raw Results: No results found")
            else:
                context_parts.append("Raw Results:\n" + "\n\n".join(summary_tables))

                # Check if we need bulk processing based on total context size
                full_context = "\n\n".join(context_parts)
                total_tokens = estimate_tokens(full_context)

                if total_tokens > max_tokens_per_request and model_bulk is not None:
                    log.info(
                        f"Context has {total_tokens} tokens, using text-based bulk processing"
                    )

                    # Use text-based chunking for already formatted tables
                    chunks = chunk_text_tables(
                        summary_tables, max_tokens_per_chunk=max_tokens_per_request
                    )

                    # Add query context to each chunk
                    query_context = f"Original Query: {query}\n\n"
                    chunks_with_context = [query_context + chunk for chunk in chunks]

                    return {
                        "context_chunks": chunks_with_context,
                    }

            # For smaller contexts or no bulk model, use regular summarization
            context = "\n\n".join(context_parts)
            return await _regular_summarize(context, query, model)

        except Exception as e:
            error_msg = f"Summary generation failed: {str(e)}"
            log.error(error_msg)
            fallback_content = (
                "Summary generation failed. Please check the execution results."
            )
            return {
                "messages": [AIMessage(content=fallback_content)],
            }

    async def _regular_summarize(
        context: str, query: str, llm_model: LanguageModelLike
    ):
        """Regular summarization for smaller contexts."""
        # Create summary prompt
        summary_prompt = get_summary_prompt(context)

        response = await llm_model.ainvoke([HumanMessage(content=summary_prompt)])

        log.info("Summary generated successfully")

        return {
            "messages": [response],
        }

    async def bulk_summarize_chunk(state: AgentState, bulk_model: LanguageModelLike):
        """Summarize a single chunk using the bulk model."""
        # This function will be called for each chunk via Send
        chunk_text = state.get("current_chunk", "")
        query = state.get("query", "")

        if not chunk_text:
            return {"chunk_summary": "No content to summarize"}

        try:
            chunk_prompt = get_chunk_summary_prompt(query or "", chunk_text)

            # Use the provided bulk model
            response = await bulk_model.ainvoke([HumanMessage(content=chunk_prompt)])

            if hasattr(response, "content"):
                summary = getattr(response, "content")
            else:
                summary = str(response)

            log.info(f"Generated chunk summary of length: {len(summary)}")
            return {"chunk_summary": summary}

        except Exception as e:
            log.error(f"Chunk summarization failed: {e}")
            return {"chunk_summary": f"Error summarizing chunk: {str(e)}"}

    async def aggregate_summaries(state: AgentState):
        """Aggregate chunk summaries using the main model."""
        query = state.get("query", "")
        chunk_summaries = state.get("chunk_summaries", [])

        if not chunk_summaries:
            error_msg = "Cannot aggregate: No chunk summaries available"
            log.error(error_msg)
            return {
                "messages": [AIMessage(content=error_msg)],
            }

        try:
            # Combine all chunk summaries
            combined_summaries = "\n\n".join(
                [
                    f"Summary {i + 1}:\n{summary}"
                    for i, summary in enumerate(chunk_summaries)
                ]
            )

            aggregate_prompt = get_aggregate_summaries_prompt(
                query or "", combined_summaries
            )
            response = await model.ainvoke([HumanMessage(content=aggregate_prompt)])

            log.info("Successfully aggregated chunk summaries")
            return {
                "messages": [response],
            }

        except Exception as e:
            error_msg = f"Summary aggregation failed: {str(e)}"
            log.error(error_msg)
            return {
                "messages": [AIMessage(content=error_msg)],
            }

    async def should_verify_plan(state: AgentState) -> str:
        """Decide if we should verify the plan or go straight to execution."""
        plan = state.get("plan")
        return "verify" if plan else "execute"

    async def should_execute_or_replan(state: AgentState) -> str:
        """Decide if we should execute, replan, or end based on validation results."""
        errors = state.get("plan_validation_errors", [])

        if not errors:
            return "execute"
        elif len(errors) > 3:  # Avoid infinite loops
            return "end"
        else:
            return "replan"

    async def should_use_bulk_processing(state: AgentState) -> str:
        """Decide whether to use bulk processing or regular summarization."""
        context_chunks = state.get("context_chunks")

        if context_chunks and len(context_chunks) > 1:
            return "bulk"
        else:
            return "regular"

    async def route_chunks_for_processing(state: AgentState):
        """Route chunks to bulk processing by processing them sequentially."""
        chunks = state.get("context_chunks", [])
        query = state.get("query", "")

        if not chunks:
            return {"chunk_summaries": []}

        # Process chunks sequentially for now (can be parallelized later)
        summaries = []
        bulk_model_to_use = model_bulk or model

        for i, chunk in enumerate(chunks):
            try:
                chunk_state = {
                    "messages": [],
                    "query": query,
                    "plan": None,
                    "executor_result": None,
                    "plan_validation_errors": None,
                    "context_chunks": None,
                    "chunk_summaries": None,
                    "current_chunk": chunk,
                    "chunk_index": i,
                }
                result = await bulk_summarize_chunk(chunk_state, bulk_model_to_use)  # type: ignore
                summaries.append(result.get("chunk_summary", ""))
                log.info(f"Processed chunk {i + 1}/{len(chunks)}")
            except Exception as e:
                log.error(f"Failed to process chunk {i}: {e}")
                summaries.append(f"Error processing chunk: {str(e)}")

        log.info(f"Completed bulk processing of {len(chunks)} chunks")
        return {"chunk_summaries": summaries}

    # Workflow setup
    workflow = StateGraph(
        state_schema=AgentState, context_schema=ContentIntelligenceInput
    )
    workflow.add_node("prepare_plan", prepare_plan)
    workflow.add_node("tools", tool_node)  # Add tool node
    workflow.add_node("process_plan", process_plan)  # Process tool results
    workflow.add_node("verify_plan", verify_plan)
    workflow.add_node("execute_plan", execute_plan)
    workflow.add_node("summarize", summarize)

    # Add bulk processing nodes
    workflow.add_node("route_chunks", route_chunks_for_processing)
    workflow.add_node("aggregate_summaries", aggregate_summaries)

    workflow.add_edge(START, "prepare_plan")

    # LLM calling the create_plan tool?
    workflow.add_conditional_edges(
        "prepare_plan",
        should_call_tools,
        {
            "tools": "tools",
            "done": END,
        },
    )

    # After tool execution, process the results
    workflow.add_edge("tools", "process_plan")

    # Plan verification flow
    workflow.add_conditional_edges(
        "process_plan",
        should_verify_plan,
        {
            "verify": "verify_plan",
            "execute": "execute_plan",
        },
    )

    # After verification, decide if we need to re-plan or execute
    workflow.add_conditional_edges(
        "verify_plan",
        should_execute_or_replan,
        {
            "execute": "execute_plan",
            "replan": "prepare_plan",
            "end": END,
        },
    )

    # After execution, go to summarization which may route to bulk processing
    workflow.add_edge("execute_plan", "summarize")

    # From summarize, check if we need bulk processing
    workflow.add_conditional_edges(
        "summarize",
        should_use_bulk_processing,
        {
            "bulk": "route_chunks",
            "regular": END,
        },
    )

    # Process chunks and aggregate results
    workflow.add_edge("route_chunks", "aggregate_summaries")
    workflow.add_edge("aggregate_summaries", END)
    return workflow.compile(
        checkpointer=checkpointer,
        store=store,
        interrupt_before=interrupt_before,
        interrupt_after=interrupt_after,
        debug=debug,
        name=name,
    )
