from __future__ import annotations

import logging
import time
from functools import singledispatchmethod
from typing import Any

import polars as pl
from pydantic import BaseModel, Field
from veri_agents_aiware.content_intelligence.adapters import SegmentAdapter
from veri_agents_aiware.content_intelligence.data import (
    Table,
    RecordsTable,
    SegmentsTable,
    TargetSelector,
    TdoTable,
    coalesce_segments,
    dedupe_segments,
    format_table_delimited,
    new_tdo_table,
)

# --- ops ---
from veri_agents_aiware.content_intelligence.ops import (
    AggregateOp,
    EvidenceOp,
    FilterOp,
    FindFaceOp,
    FindLogoOp,
    # FIND
    FindTranscriptOp,
    GetTdoFacesOp,
    GetTdoLogosOp,
    # GET_TDO
    GetTdoTranscriptOp,
    JoinTemporalOp,
    MergeOp,
    OutputOp,
    SortSpec,
    # tables/timeline ops
    ProjectOp,
)
from veri_agents_aiware.content_intelligence.plan import InvalidPlanError
from veri_agents_aiware.content_intelligence.temporal import join_temporal

log = logging.getLogger(__name__)


class Evidence(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    primary: dict[str, Any]  # A single row/record from the segments table
    supporting: SegmentsTable = Field(default_factory=lambda: pl.DataFrame())
    reason: str | None = None


class ErrorInfo(BaseModel):
    stage: str
    message: str


class State(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    query: str
    target: TargetSelector
    plan: Any | None = None
    tdo_table: TdoTable | None = None
    segments_tables: dict[str, SegmentsTable] = {}
    records_tables: dict[str, RecordsTable] = {}
    evidence: list[Evidence] = []
    answer: Any = None
    errors: list[ErrorInfo] = []
    started_at: float = Field(default_factory=time.time)


# ----------------------- EXECUTOR -----------------------

class Executor:
    """Deterministic executor for Plan steps with singledispatch-based handlers."""

    def __init__(self, segment_adapter: SegmentAdapter):
        self.segment_adapter = segment_adapter

    # ---------------------- public ----------------------

    async def run(self, state: State) -> State:
        if not state.plan:
            state.errors.append(ErrorInfo(stage="executor", message="missing plan"))
            return state
        try:
            for step in state.plan.steps:
                log.debug("Executing %s: %s", type(step).__name__, step)
                await self._handle(step, state)  # dispatch on step type
        except Exception as e:
            log.exception("Executor error")
            state.errors.append(ErrorInfo(stage="execute", message=str(e)))
        return state

    # ---------------------- dispatch root ----------------------

    @singledispatchmethod
    async def _handle(self, step: BaseModel, state: State) -> None:
        raise NotImplementedError(f"No handler for {type(step).__name__}")

    # ---------------------- FIND handlers ----------------------

    @_handle.register
    async def _handle_find_transcript(
        self, step: FindTranscriptOp, state: State
    ) -> None:
        segs = await self.segment_adapter.find_transcript(step, state.target)
        state.segments_tables[step.output] = segs

    @_handle.register
    async def _handle_find_face(self, step: FindFaceOp, state: State) -> None:
        segs = await self.segment_adapter.find_face(step, state.target)
        state.segments_tables[step.output] = segs

    @_handle.register
    async def _handle_find_logo(self, step: FindLogoOp, state: State) -> None:
        segs = await self.segment_adapter.find_logo(step, state.target)
        state.segments_tables[step.output] = segs

    # ---------------------- GET_TDO handlers ----------------------

    @_handle.register
    async def _handle_get_tdo_transcript(
        self, step: GetTdoTranscriptOp, state: State
    ) -> None:
        segs = await self.segment_adapter.get_tdo_transcript(step, state.target)
        state.segments_tables[step.output] = segs

    @_handle.register
    async def _handle_get_tdo_faces(self, step: GetTdoFacesOp, state: State) -> None:
        segs = await self.segment_adapter.get_tdo_faces(step, state.target)
        state.segments_tables[step.output] = segs

    @_handle.register
    async def _handle_get_tdo_logos(self, step: GetTdoLogosOp, state: State) -> None:
        segs = await self.segment_adapter.get_tdo_logos(step, state.target)
        state.segments_tables[step.output] = segs

    # ---------------------- timeline/table ops ----------------------

    @_handle.register
    async def _handle_project(self, step: ProjectOp, state: State) -> None:
        segs = state.segments_tables.get(step.input)
        if segs is None:
            raise InvalidPlanError(
                f"PROJECT input alias '{step.input}' not found in segments_tables"
            )
        proj = segs.select(
            [pl.col(p.input_field).alias(p.output_field) for p in step.select]
        )
        state.records_tables[step.output] = proj

    @_handle.register
    async def _handle_filter(self, step: FilterOp, state: State) -> None:
        def ok(row: dict[str, Any], conds: dict[str, Any]) -> bool:
            for field, rule in conds.items():
                val = row.get(field)
                if isinstance(rule, dict):
                    if "eq" in rule and val != rule["eq"]:
                        return False
                    if "gte" in rule and not (val is not None and val >= rule["gte"]):
                        return False
                    if "lte" in rule and not (val is not None and val <= rule["lte"]):
                        return False
                else:
                    if val != rule:
                        return False
            return True

        src = state.records_tables.get(step.input, [])
        state.records_tables[step.output] = [r for r in src if ok(r, step.where)]

    @_handle.register
    async def _handle_join_temporal(self, step: JoinTemporalOp, state: State) -> None:
        REQUIRED_COLS = {"tdo_id", "start_s", "end_s"}

        def _ensure_cols(df: pl.DataFrame, alias: str) -> None:
            missing = REQUIRED_COLS - set(df.columns)
            if missing:
                raise InvalidPlanError(
                    f"JOIN_TEMPORAL: alias '{alias}' is missing required columns {sorted(missing)}"
                )

        left_df = state.segments_tables.get(step.left)
        if left_df is None:
            raise InvalidPlanError(
                f"JOIN_TEMPORAL left alias '{step.left}' not found in segments_tables"
            )
        right_df = state.segments_tables.get(step.right)
        if right_df is None:
            raise InvalidPlanError(
                f"JOIN_TEMPORAL right alias '{step.right}' not found in segments_tables"
            )

        _ensure_cols(left_df, step.left)
        _ensure_cols(right_df, step.right)

        # Temporal semi-join: keep only left rows that satisfy the relation with at least one right row
        matched_left = join_temporal(
            left=left_df,
            right=right_df,
            relation=step.relation,  # "BEFORE" | "AFTER" | "OVERLAPS" | "WITHIN"
            within_s=step.within_s,  # may be None
            tol=float(step.tolerance_s),  # default 0.0
            how="pairs",
        )

        # dedup exact duplicates on the core identity+time
        subset = [
            c
            for c in ("tdo_id", "start_s", "end_s", "signal", "channel", "label")
            if c in matched_left.columns
        ]
        if subset:
            matched_left = matched_left.unique(subset=subset)
        state.segments_tables[step.output] = matched_left

    @_handle.register
    async def _handle_merge(self, step: MergeOp, state: State) -> None:
        """Merge multiple segment tables, then dedupe or coalesce them."""
        dfs: list[SegmentsTable] = []
        for alias in step.inputs:
            try:
                dfs.append(state.segments_tables[alias])
            except KeyError:
                raise InvalidPlanError(
                    f"MERGE input alias '{alias}' not found in segments_tables"
                )
        if not dfs:
            raise InvalidPlanError("MERGE did not have any input data")

        merged: SegmentsTable = pl.concat(dfs, how="diagonal", rechunk=True)

        tol = step.tolerance_s if step.tolerance_s and step.tolerance_s > 0.0 else 0.0
        if step.coalesce:
            result: SegmentsTable = coalesce_segments(merged, tolerance_s=tol)
        else:
            # dedupe_segments handles its own key creation
            result: SegmentsTable = dedupe_segments(merged, tol=tol)

        state.segments_tables[step.output] = result

    async def _get_table_from_state(self, state: State, alias: str) -> Table:
        # Try segments first, then records. Adjust to your State layout.
        if alias in state.segments_tables:
            return state.segments_tables[alias]
        if alias in state.records_tables:
            return state.records_tables[alias]
        # tdo metadata table?
        if alias == "_tdo_metadata":
            if state.tdo_table is None:
                tdos = await self.segment_adapter.get_tdos(
                    state.target, include_segments=False
                )
                state.tdo_table = new_tdo_table([tdo.as_tdo_dict() for tdo in tdos])
            return state.tdo_table
        raise InvalidPlanError(f"Unknown input alias '{alias}'")

    def _duration_expr(self) -> pl.Expr:
        # Helper used in exprs below
        return (pl.col("end_s") - pl.col("start_s")).cast(pl.Float64)

    def _compile_metric_expr(
        self, field: str | None, expr: str | None
    ) -> pl.Expr | None:
        """
        Compile a safe metric base expression.
        Supported:
        - field="score" → pl.col("score")
        - expr="duration()"  → end_s - start_s
        - expr="end_s - start_s" (alias)
        """
        if field:
            return pl.col(field)

        if expr:
            e = expr.strip().lower()
            if e == "duration()" or e == "end_s - start_s":
                return self._duration_expr()
            # (Optionally extend here with whitelisted cols / arithmetic.)
            raise ValueError(f"Unsupported expr: {expr!r}")

        # no field and no expr → allowed only for count()
        return None  # caller must handle this

    def _compile_metric_agg(self, name: str, spec: dict) -> pl.Expr:
        """
        Turn a single metric spec into a Polars aggregation expression with alias `name`.
        """
        fn = spec.get("fn")
        field = spec.get("field")
        expr = spec.get("expr")

        base = self._compile_metric_expr(field, expr)
        if fn == "count":
            return pl.count().alias(name)
        elif fn == "count_distinct":
            if base is None:
                raise InvalidPlanError(f"count_distinct for '{name}' needs field/expr")
            return base.n_unique().alias(name)
        elif fn == "sum":
            if base is None:
                raise InvalidPlanError(f"sum for '{name}' needs field/expr")
            return base.sum().alias(name)
        elif fn == "avg":
            if base is None:
                raise InvalidPlanError(f"avg for '{name}' needs field/expr")
            return base.mean().alias(name)
        elif fn == "min":
            if base is None:
                raise InvalidPlanError(f"min for '{name}' needs field/expr")
            return base.min().alias(name)
        elif fn == "max":
            if base is None:
                raise InvalidPlanError(f"max for '{name}' needs field/expr")
            return base.max().alias(name)

        raise InvalidPlanError(f"Unsupported fn '{fn}' for metric '{name}'")

    @_handle.register
    async def handle_aggregate(self, step: AggregateOp, state) -> None:
        df = await self._get_table_from_state(state, step.input)

        # Build aggregation expressions
        aggs = []
        for name, spec in step.metrics.items():
            aggs.append(self._compile_metric_agg(name, spec))

        if step.group_by:
            out = df.group_by(step.group_by).agg(aggs)
        else:
            out = df.select(aggs)
        state.segments_tables[step.output] = out

    @_handle.register
    async def _handle_evidence(self, step: EvidenceOp, state: State) -> None:
        segs = state.segments_tables.get(step.input)
        if segs is None:
            raise InvalidPlanError(
                f"EVIDENCE input alias '{step.input}' not found in segments_tables"
            )
        state.records_tables["_evidence"] = segs

    async def _get_structured_table_data(
        self,
        step: OutputOp,
        state: State,
        alias: str,
        sort_spec: SortSpec | None = None,
        table: Table | None = None,
    ) -> dict[str, Any]:
        """Get structured table data for output, with optional sorting and limiting.
         
         Args:
            step: The OutputOp step.
            state: The current State.
            alias: The alias of the table to get data for.
            sort_spec: Optional SortSpec to sort the table.
            table: Optional Table to use directly instead of looking up alias.

         Returns:
            A dictionary containing structured table data.
        """
        # Check if table exists and not empty
        if table is None:
            try:
                table = await self._get_table_from_state(state, alias)
            except InvalidPlanError:
                return {
                    "alias": alias,
                    "status": "missing",
                    "data": None,
                    "shape": (0, 0),
                    "columns": [],
                }

        if table.is_empty():
            return {
                "alias": alias,
                "status": "empty", 
                "data": None,
                "shape": (0, table.width),
                "columns": list(table.columns),
            }

        # Sort and limit the table
        processed_table = table
        if sort_spec and sort_spec.field in table.columns:
            processed_table = processed_table.sort(sort_spec.field, descending=not sort_spec.ascending)
        
        # Apply row limit if specified
        if step.limit and step.limit > 0:
            processed_table = processed_table.head(step.limit)

        # Remove columns that are all null
        non_null_cols = [c for c in processed_table.columns if processed_table[c].null_count() < processed_table.height]
        if non_null_cols:
            processed_table = processed_table.select(non_null_cols)

        return {
            "alias": alias,
            "status": "ok",
            "data": processed_table,
            "shape": (processed_table.height, processed_table.width),
            "columns": list(processed_table.columns),
        }

    async def _format_table(
        self,
        step: OutputOp,
        state: State,
        alias: str,
        sort_spec: SortSpec | None = None,
        table: Table | None = None,
    ) -> str:
        """ Format a table for output, with optional sorting and limiting.
         If table is provided, use it directly; otherwise look up alias in state.
         
         Args:
            step: The OutputOp step.
            state: The current State.
            alias: The alias of the table to format.
            sort_spec: Optional SortSpec to sort the table.
            table: Optional Table to use directly instead of looking up alias.

         Returns:
            A string representation of the table.
        """
        # Get structured data and format it
        structured_data = await self._get_structured_table_data(step, state, alias, sort_spec, table)
        
        alias = structured_data["alias"]
        status = structured_data["status"]
        shape = structured_data["shape"]
        
        ret = f"{alias} ({shape[0]}, {shape[1]}) = \n"
        
        if status == "missing":
            return ret + "<missing>\n"
        elif status == "empty":
            return ret + "(empty)\n"
        
        table_data = structured_data["data"]
        body = format_table_delimited(
            table_data,
            delimiter="\t",
            text_preview=None,
            round_digits=4,
            add_footer=True,
            limit_rows=step.limit,
        )
        return ret + body

    @_handle.register
    async def _handle_output(self, step: OutputOp, state: State) -> None:
        log.info("SEGMENTS TABLES:")
        for table in state.segments_tables.keys():
            log.info("\n%s", await self._format_table(step, state, table))
        log.info("RECORDS TABLES:")
        for table in state.records_tables.keys():
            log.info("\n%s", await self._format_table(step, state, table))

        # Return structured data instead of formatted strings
        structured_summary = []
        for alias, sort_spec in step.summary_from:
            table_data = await self._get_structured_table_data(step, state, alias, sort_spec=sort_spec)
            structured_summary.append(table_data)

        state.answer = {
            "summary": structured_summary,
            # Keep a formatted version for backwards compatibility / debugging
            "summary_formatted": [
                await self._format_table(step, state, alias, sort_spec=sort_spec)
                for alias, sort_spec in step.summary_from
            ],
        }

