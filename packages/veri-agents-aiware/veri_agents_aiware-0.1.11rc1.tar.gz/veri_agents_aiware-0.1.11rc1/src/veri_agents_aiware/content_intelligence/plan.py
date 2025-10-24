from __future__ import annotations
import hashlib
import json
import logging
from typing import Any, Type, Literal

from pydantic import BaseModel, Field, ConfigDict
from langchain_core.tools import BaseTool

from veri_agents_aiware.content_intelligence.ops import DiscriminatedOp
from veri_agents_aiware.content_intelligence.data import SEGMENT_SCHEMA, TDO_SCHEMA, Signal

log = logging.getLogger(__name__)

class InvalidPlanError(Exception):
    pass

class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_version: str = "1.0"
    steps: list[DiscriminatedOp]

    def signature(self) -> str:
        body = self.model_dump_json(by_alias=True)
        return hashlib.sha256(body.encode()).hexdigest()[:16]

    def prettify(self) -> str:
        s = ""
        for step in self.steps:
            s += f"- {step.op}({', '.join(f'{k}={v}' for k, v in step.model_dump().items() if v)})\n"
        return s


class CreatePlanTool(BaseTool):
    """Tool for creating execution plans with proper validation."""

    name: str = "create_plan"
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"
    description: str = f"""Create an execution plan for aiWARE media analysis queries.
    
    Definitions:
      - A Plan is a sequence of operations (ops) to be executed on a set of target TDOs.
      - A TDO is a temporal data object, a container for media assets and their associated metadata and analysis results.

    Procedure:
      - Initially use FIND or GET ops to retrieve TDO segment tables of interest.
      - TDO Segments have the following fields: {SEGMENT_SCHEMA.keys()}.
      - Note that which fields are filled depends on which GET or FIND operations were used to create the segments, for example GET_TDO_FACES will have 'label' set while GET_TDO_TRANSCRIPT will have 'transcript' set.
        The 'label' field contains names for faces, logos, objects, etc. The 'transcript' field contains text for transcript or OCR segments.
        'score' contains confidence values (0.0 to 1.0) if available.
      - Avoid running OUTPUT on raw segment tables as they will typically be too large for your context window.
      - Use ops like MERGE, JOIN_TEMPORAL, AGGREGATE to process and combine the segment tables into record tables containing exactly the data you need to answer the query.
      - If you know which fields you will need (e.g. only the transcript) use PROJECT to further reduce token usage.
      - When you have retrieved and transformed the data, use OUTPUT to return results from tables or segments to the LLM.
      - OUTPUT multiple aliases if needed - for example get a list of persons and then also the aggregate statistics.
      - Internal aliases start with "_" and you can access those as well in all operations. 
        The only internal alias currently is "_tdo_metadata" which contains basic TDO metadata with the following fields: {TDO_SCHEMA.keys()}.
        Example to retrieve the 5 longest TDOs: OUTPUT(summary_from=[('_tdo_metadata', {{'field': 'duration_s', 'ascending': False}})], limit=5)

    Common patterns:
      - Screen time: FIND_FACE → MERGE → AGGREGATE → OUTPUT
      - Count persons: GET_TDO_FACES → AGGREGATE (with count_distinct) → OUTPUT
      - List persons: GET_TDO_FACES → AGGREGATE (with group_by) → OUTPUT
      - Text search: FIND_TRANSCRIPT → OUTPUT
      - Temporal: FIND_X → FIND_Y → JOIN_TEMPORAL → OUTPUT
      - Summaries or translations: GET_TDO_TRANSCRIPT ("utterance" or "full" granularity) → PROJECT (only get transcript field, timestamps if needed) → OUTPUT

    ALWAYS try to keep your context window small by aggregating tables when possible (like don't output GET_TDO_FACES directly if you just want to know unique persons).

    Signals can be: {', '.join(Signal.__args__)}.
    """

    class CreatePlanInput(BaseModel):
        """Input for creating a plan."""

        plan: Plan = Field(
            description="The execution plan with a sequence of operations"
        )
        reasoning: str = Field(
            description="Brief explanation of why this plan was chosen for the query"
        )

    args_schema: Type[BaseModel] = CreatePlanInput  # pyright: ignore[reportIncompatibleVariableOverride]

    def _run(self, plan: Plan, reasoning: str) -> tuple[str, dict[str, Any]]:
        """Create and validate a plan."""
        try:
            # Handle both Plan objects and dictionaries
            if isinstance(plan, dict):
                # Convert dict to Plan object
                validated_plan = Plan.model_validate(plan)
            else:
                # Already a Plan object, validate it
                validated_plan = Plan.model_validate(plan.model_dump(by_alias=True))

            result = {
                "success": True,
                "plan": validated_plan.model_dump(by_alias=True),
                "reasoning": reasoning,
                "plan_signature": validated_plan.signature(),
                "num_steps": len(validated_plan.steps),
            }

            log.info(f"Plan created successfully: {len(validated_plan.steps)} steps")

            message = f"Created plan:\n\n{str(plan.prettify()) if plan else 'No valid plan'}.\n\nReasoning: {reasoning if reasoning else 'N/A'}."
            return message, result

        except Exception as e:
            error_result = {"success": False, "error": str(e), "reasoning": reasoning}
            log.error(f"Plan creation failed: {e}")
            return f"Error: {str(e)}", error_result

