from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

from veri_agents_aiware.content_intelligence.data import (
    Signal,
    TextGranularity,
)

ConstraintRelation = Literal["BEFORE", "AFTER", "OVERLAPS", "WITHIN"]

# ---------------------------
# Time window helper types
# ---------------------------


class MediaTime(BaseModel):
    """Relative to the TDO's own timeline (seconds)."""

    from_s: Optional[float] = None
    to_s: Optional[float] = None


class AbsTime(BaseModel):
    """Wall-clock constraints for selecting WHICH TDOs (ISO strings or epoch seconds)."""

    from_iso: Optional[str] = None
    to_iso: Optional[str] = None
    from_epoch_s: Optional[float] = None
    to_epoch_s: Optional[float] = None


# -----------------------------
# Find Ops (base NOT exported)
# -----------------------------


class _FindOpBase(BaseModel):
    """Common fields for all FIND_* ops. Not exposed to the LLM union."""

    output: str
    media_time: Optional[MediaTime] = None
    abs_time: Optional[AbsTime] = None


# ---------------------------
# Concrete FIND ops
# ---------------------------


class FindTranscriptOp(_FindOpBase):
    """Do classic keyword search on transcripts."""

    op: Literal["FIND_TRANSCRIPT"] = "FIND_TRANSCRIPT"
    # mode: Literal["exhaustive", "semantic", "hybrid"] = "hybrid"
    query: str = Field(
        ...,
        description="Search query string for finding transcript text.",
        examples=["specific phrase", '"kobe bryant" AND (basketball OR lakers)'],
    )
    granularity: TextGranularity = "window"
    # speaker: Optional[str] = None


class FindFaceOp(_FindOpBase):
    # TODO: do we want to be able to provide multiple entityIds?
    """Find specific faces/persons. Use this if given an entity ID or name."""

    op: Literal["FIND_FACE"] = "FIND_FACE"
    where: Dict[str, Any] = Field(
        default_factory=dict,
        description='Search criteria for finding faces. Can be by {"entityId":"..."} or {"name":"..."}.',
    )
    #min_score: float = 0.0


class FindLogoOp(_FindOpBase):
    """Find specific logos/brands. Use this if given an entity ID or name."""

    op: Literal["FIND_LOGO"] = "FIND_LOGO"
    where: Dict[str, Any] = Field(
        default_factory=dict,
        description='Search criteria for finding logos. Can be by {"entityId":"..."} or {"name":"..."}.',
    )


# (Optional future)
# class FindObjectOp(_FindOpBase): ...
# class FindOcrOp(_FindOpBase): ...


# ---------------------------
# GET_TDO ops
# ---------------------------


class GetTdoFacesOp(BaseModel):
    """Get all occurrences of faces/persons in the TDOs. 
       If you need unique occurrences, use the aggregate operation after this.
       Use this if you don't have a specific name or entity ID.
    """

    op: Literal["GET_TDO_FACES"] = "GET_TDO_FACES"
    output: str


class GetTdoLogosOp(BaseModel):
    """Get all logo occurrences in the TDOs.
       If you need unique occurrences, use the aggregate operation after this.
    Use this if you don't have a specific name or entity ID."""

    op: Literal["GET_TDO_LOGOS"] = "GET_TDO_LOGOS"
    output: str


class GetTdoTranscriptOp(BaseModel):
    """Get the speech transcript for the target TDOs."""

    op: Literal["GET_TDO_TRANSCRIPT"] = "GET_TDO_TRANSCRIPT"
    output: str
    # probably add "sentence" or "words" if needed (unlikely?)
    granularity: Literal["utterance", "full"] = Field(
        default="utterance",
        description="Granularity of the returned transcript, e.g. 'utterance' for speaker segments (if we have speaker information, otherwise inter-pausal units), 'full' for the entire transcript as one segment.",
    )
    # speaker: Optional[str] = None


# ---------------------------
# Table/Timeline ops
# ---------------------------


class Projection(BaseModel):
    """Represents a projection of fields from the input in a segment to the output in a table."""

    input_field: str
    output_field: str


class ProjectOp(BaseModel):
    """Projects segments to a table of records with custom fields."""

    op: Literal["PROJECT"] = "PROJECT"
    input: str = Field(
        ..., description="Alias to read from. Must refer to a segments table alias."
    )
    output: str = Field(
        ..., description="Alias to write the projected records table to."
    )
    select: list[Projection]


class FilterOp(BaseModel):
    """Filter rows in a records table by conditions."""

    op: Literal["FILTER"] = "FILTER"
    input: str
    output: str
    where: Dict[str, Any]


class JoinTemporalOp(BaseModel):
    """Temporal join between two segment tables, for example to find segments where a logo has been shown at the same time as a face.
    The join is scoped by tdo_id, so only segments from the same TDO are considered for joining.
    Right-side joined columens get a "_right" suffix, so if you join faces with logos, the face names will be in "label" and the logo names in "label_right".
    """

    op: Literal["JOIN_TEMPORAL"] = "JOIN_TEMPORAL"
    left: str = Field(..., description="Alias of the left-side segments table to join.")
    right: str = Field(..., description="Alias of the right-side segments table to join with. The fields of this table will get a '_right' suffix, e.g. 'label_right'.")
    output: str = Field(..., description="Alias to write the joined segments table to.")
    relation: ConstraintRelation
    within_s: Optional[float] = None
    tolerance_s: float = 0.0


class MergeOp(BaseModel):
    """Merge adjacent segments (e.g. a segment from second 2 to 3 and another one from 3 to 5 would be merged into one segment 2 to 5)"""

    op: Literal["MERGE"] = "MERGE"
    inputs: List[str]
    output: str
    tolerance_s: float = 0.0
    coalesce: bool = Field(
        default=True,
        description="If true, coalesce non-time fields (e.g. label), otherwise just deduplicate.",
    )


class AggregateOp(BaseModel):
    """
    Aggregate rows from a segments/table alias into a new summary table.

    - input:   alias of an existing Polars DF (segments or records)
    - output:  alias for the aggregated DF
    - group_by: columns to group on (e.g., ["label"], ["tdo_id","signal"])
    - metrics:  name -> {"fn": <count|count_distinct|sum|avg|min|max>,
                         "field": <col>,                # optional, e.g. "score"
                         "expr": <safe expr string>}    # optional, e.g. "duration()" or "end_s - start_s"

      Rules:
        • Provide either 'field' or 'expr' (or neither for count()).
        • Supported exprs: "duration()", "end_s - start_s".
          (Extendable; see _compile_metric_expr below.)
    """

    op: Literal["AGGREGATE"] = "AGGREGATE"
    input: str = Field(
        ...,
        description="Alias to read from. Must refer to a segments or records alias.",
    )
    output: str = Field(
        ..., description="Alias to write the aggregated records table to."
    )
    group_by: list[str] = Field(
        default_factory=list
    )  # probably SegmentFieldStr but if it's operating on a records table?
    metrics: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        examples=[
            {
                "rows": {"fn": "count"},
                "screen_time_s": {"fn": "sum", "expr": "duration()"},
                "avg_conf": {"fn": "avg", "field": "score"},
                "distinct_tdos": {"fn": "count_distinct", "field": "tdo_id"},
            }
        ],
    )


class EvidenceOp(BaseModel):
    """Extract evidence segments for logging relevant segments."""

    op: Literal["EVIDENCE"] = "EVIDENCE"
    input: str = Field(
        ..., description="Alias to read from. Must refer to a segments alias."
    )
    fields: List[str] | None = Field(
        default=None,
        description="List of field names to include, when None include all standard fields.",
    )
    limit_per_tdo: int = 100


class SortSpec(BaseModel):
    field: str
    ascending: bool = True


class OutputOp(BaseModel):
    op: Literal["OUTPUT"] = "OUTPUT"
    summary_from: list[tuple[str, SortSpec | None]] = Field(
        description="List of table aliases to return to the LLM, for each table a sort spec or None for no sorting. Use the special name _tdo_metadata to access the TDO metadata table.",
    )

    limit: int = Field(
        default=1000,
        ge=1,
        description="Maximum number of rows to return per summary table.",
    )


# ---------------------------------------------
# Unions (exported to the planner / LLM)
# ---------------------------------------------

# Everything the LLM is allowed to emit:
Op = Union[
    # FIND
    FindTranscriptOp,
    FindFaceOp,
    FindLogoOp,
    # GET_TDO
    GetTdoTranscriptOp,
    GetTdoFacesOp,
    GetTdoLogosOp,
    # tables/timeline
    ProjectOp,
    # TODO: not implemented yet
    # FilterOp,
    JoinTemporalOp,
    MergeOp,
    AggregateOp,
    #EvidenceOp,
    OutputOp,
]

DiscriminatedOp = Annotated[Op, Field(discriminator="op")]
