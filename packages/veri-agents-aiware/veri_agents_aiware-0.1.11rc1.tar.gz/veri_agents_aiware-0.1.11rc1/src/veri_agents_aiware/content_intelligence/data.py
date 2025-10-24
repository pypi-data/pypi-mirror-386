from __future__ import annotations
from typing import Any, Literal, Annotated, TypeAlias, Union
import hashlib
from datetime import datetime

from pydantic import BaseModel, Field
import polars as pl

Channel = Literal["audio", "video", "image", "text"]
Signal = Literal[
    "transcript",
    "face",
    "logo",
    "object",
    "ocr",
    "speaker",
    "keyword",
    "shot",
    "music_cue",
    "unknown",
]
TextGranularity = Literal["window", "token", "word", "sentence"]

# ---------------------------
# TDO target selectors
# ---------------------------


class TargetByOrg(BaseModel):
    """Operations target all TDOs in the org"""

    kind: Literal["org"]


class TargetByIds(BaseModel):
    """Operations target specific TDOs by their IDs"""

    kind: Literal["tdo_ids"]
    tdo_ids: list[str]


class TargetByFolder(BaseModel):
    """Operations target TDOs in a specific folder"""

    kind: Literal["folder"]
    folder_id: str | None = None
    folder_name: str | None = None
    # created_after: str | None = None  # ISO8601
    # created_before: str | None = None


TargetSelector = Annotated[
    Union[TargetByOrg, TargetByIds, TargetByFolder],
    Field(discriminator="kind"),
]

# ---------------------------
# Data tables
# ---------------------------

Table: TypeAlias = pl.DataFrame
TdoTable: TypeAlias = pl.DataFrame
SegmentsTable: TypeAlias = pl.DataFrame
RecordsTable: TypeAlias = pl.DataFrame

SEGMENT_SCHEMA = {
    "tdo_id": pl.Utf8,
    "start_s": pl.Float64,
    "end_s": pl.Float64,
    "channel": pl.Utf8,
    "signal": pl.Utf8,
    "transcript": pl.Utf8,
    "score": pl.Float64,
    "label": pl.Utf8,
    "engine_id": pl.Utf8,
    "engine_name": pl.Utf8,
    "abs_start_epoch_s": pl.Float64,
    "abs_end_epoch_s": pl.Float64,
    # keep nested as JSON text unless you need to compute on them
    "bbox_json": pl.Utf8,  # json.dumps(bbox) or None
    "poly_json": pl.Utf8,  # json.dumps(poly) or None
    "meta_json": pl.Utf8,  # json.dumps(meta) or None
}


def _serialize_value(obj):
    """Custom JSON serializer that handles datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_value(item) for item in obj]
    else:
        return obj


def create_segment_dict(
    tdo_id: str,
    start_s: float,
    end_s: float,
    *,
    channel: str = "video",
    signal: str = "transcript",
    score: float | None = 0.0,
    label: str | None = None,
    transcript: str | None = None,
    engine_id: str | None = None,
    engine_name: str | None = None,
    abs_start_epoch_s: float | None = None,
    abs_end_epoch_s: float | None = None,
    bbox: dict[str, float] | None = None,
    poly: list[dict] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a segment dictionary that can be used with new_segment()."""
    import json

    return {
        "tdo_id": tdo_id,
        "start_s": start_s,
        "end_s": end_s,
        "channel": channel,
        "signal": signal,
        "score": score,
        "label": label,
        "transcript": transcript,
        "engine_id": engine_id,
        "engine_name": engine_name,
        "abs_start_epoch_s": abs_start_epoch_s,
        "abs_end_epoch_s": abs_end_epoch_s,
        "bbox_json": json.dumps(bbox) if bbox else None,
        "poly_json": json.dumps(poly) if poly else None,
        "meta_json": json.dumps(_serialize_value(meta)) if meta else None,
    }


TDO_SCHEMA = {
    "tdo_id": pl.Utf8,
    "tdo_name": pl.Utf8,
    "created_datetime": pl.Datetime,
    "asset_type": pl.Utf8,
    "start_datetime": pl.Datetime,
    "stop_datetime": pl.Datetime,
    "duration_s": pl.Float64,
}


def create_tdo_dict(
    tdo_id: str,
    tdo_name: str | None = None,
    created_datetime: datetime | None = None,
    start_datetime: datetime | None = None,
    stop_datetime: datetime | None = None,
    duration_s: float | None = None,
    asset_type: str | None = None,
) -> dict[str, Any]:
    """Create a TDO dictionary that can be used with new_tdo_table()."""
    return {
        "tdo_id": tdo_id,
        "tdo_name": tdo_name,
        "created_datetime": created_datetime,
        "asset_type": asset_type,
        "start_datetime": start_datetime,
        "stop_datetime": stop_datetime,
        "duration_s": duration_s,
    }


SegmentFieldStr = Annotated[
    str,
    Field(
        json_schema_extra={"enum": list(SEGMENT_SCHEMA.keys())},
        description="Must be one of the listed segment fields.",
    ),
]

TdoFieldStr = Annotated[
    str,
    Field(
        json_schema_extra={"enum": list(TDO_SCHEMA.keys())},
        description="Must be one of the listed TDO fields.",
    ),
]


def new_segments_table(rows: list[dict]) -> SegmentsTable:
    """Create a typed DF; missing keys become nulls."""
    return pl.DataFrame(rows, schema=SEGMENT_SCHEMA)


def new_tdo_table(rows: list[dict]) -> TdoTable:
    """Create a typed DF; missing keys become nulls."""
    return pl.DataFrame(rows, schema=TDO_SCHEMA)


# ==================
# Utility functions
# ==================


def dedupe_segments(segs: pl.DataFrame, tol: float = 0.0) -> pl.DataFrame:
    """Deduplicate segments based on tdo_id, start_s, and end_s with tolerance."""
    if segs.is_empty():
        return segs

    # Create a unique key based on tdo_id and rounded start/end times
    tolerance_factor = max(1e-6, tol + 1e-6)

    return (
        segs.with_columns(
            [
                pl.col("start_s")
                .truediv(tolerance_factor)
                .round(3)
                .alias("_start_key"),
                pl.col("end_s").truediv(tolerance_factor).round(3).alias("_end_key"),
            ]
        )
        .unique(subset=["tdo_id", "_start_key", "_end_key"], keep="first")
        .drop(["_start_key", "_end_key"])
    )


def concat_segments(segment1, segment2):
    """Concatenate two segments, modifying segment1 in place and returning it.

    Args:
        segment1: The first segment (will be modified)
        segment2: The second segment to merge into the first

    Returns:
        The modified segment1
    """
    # Time bounds - extend to cover both segments
    segment1["end_s"] = max(segment1["end_s"], segment2["end_s"])

    # Score - take the maximum
    segment1["score"] = max(
        segment1.get("score", 0.0) or 0.0, segment2.get("score", 0.0) or 0.0
    )

    # Transcript - concatenate with space separator if both exist
    transcript1 = segment1.get("transcript") or ""
    transcript2 = segment2.get("transcript") or ""
    if transcript1 and transcript2:
        segment1["transcript"] = f"{transcript1} {transcript2}"
    elif transcript2:  # Only segment2 has transcript
        segment1["transcript"] = transcript2
    # If only segment1 has transcript or both are empty, keep segment1's value

    # Label - concatenate with comma separator if both exist and different
    label1 = segment1.get("label") or ""
    label2 = segment2.get("label") or ""
    if label1 and label2 and label1 != label2:
        segment1["label"] = f"{label1}, {label2}"
    elif label2 and not label1:  # Only segment2 has label
        segment1["label"] = label2
    # If only segment1 has label or both are same/empty, keep segment1's value

    # Engine info - prefer non-null values, segment1 takes priority
    if not segment1.get("engine_id") and segment2.get("engine_id"):
        segment1["engine_id"] = segment2["engine_id"]
    if not segment1.get("engine_name") and segment2.get("engine_name"):
        segment1["engine_name"] = segment2["engine_name"]

    # Absolute time bounds - extend to cover both segments
    if (
        segment1.get("abs_start_epoch_s") is not None
        and segment2.get("abs_start_epoch_s") is not None
    ):
        segment1["abs_start_epoch_s"] = min(
            segment1["abs_start_epoch_s"], segment2["abs_start_epoch_s"]
        )
    elif segment2.get("abs_start_epoch_s") is not None:
        segment1["abs_start_epoch_s"] = segment2["abs_start_epoch_s"]

    if (
        segment1.get("abs_end_epoch_s") is not None
        and segment2.get("abs_end_epoch_s") is not None
    ):
        segment1["abs_end_epoch_s"] = max(
            segment1["abs_end_epoch_s"], segment2["abs_end_epoch_s"]
        )
    elif segment2.get("abs_end_epoch_s") is not None:
        segment1["abs_end_epoch_s"] = segment2["abs_end_epoch_s"]

    # Spatial info (bbox_json, poly_json) - keep segment1's values
    # These are typically frame-specific, so we keep the first segment's spatial data
    # If segment1 doesn't have spatial data but segment2 does, use segment2's
    if not segment1.get("bbox_json") and segment2.get("bbox_json"):
        segment1["bbox_json"] = segment2["bbox_json"]
    if not segment1.get("poly_json") and segment2.get("poly_json"):
        segment1["poly_json"] = segment2["poly_json"]

    # Metadata - merge JSON objects if both exist, otherwise prefer non-null
    import json

    meta1_str = segment1.get("meta_json")
    meta2_str = segment2.get("meta_json")

    if meta1_str and meta2_str:
        try:
            meta1 = json.loads(meta1_str)
            meta2 = json.loads(meta2_str)
            if isinstance(meta1, dict) and isinstance(meta2, dict):
                # Merge dictionaries, segment2 values override segment1
                merged_meta = {**meta1, **meta2}
                segment1["meta_json"] = json.dumps(merged_meta)
            else:
                # If not both dicts, keep segment1's metadata
                pass
        except (json.JSONDecodeError, TypeError):
            # If JSON parsing fails, keep segment1's metadata
            pass
    elif meta2_str and not meta1_str:
        segment1["meta_json"] = meta2_str

    return segment1


def coalesce_segments(
    segments: SegmentsTable, tolerance_s: float | None = 0.25
) -> SegmentsTable:
    """Coalesce adjacent segments with the same tdo_id and signal within tolerance.
    If tolerance_s is None, coalesce all adjacent segments regardless of gap.

    Args:
        segments: Input segments DataFrame.
        tolerance_s: Maximum gap in seconds to consider segments as adjacent. If None, coalesce all adjacent segments.

    Returns:
        Coalesced segments DataFrame.
    """
    if segments.is_empty():
        return segments

    # Sort by tdo_id, signal, and start_s
    sorted_df = segments.sort(["tdo_id", "signal", "start_s"])

    # Use a more efficient groupby approach
    result_rows = []

    # we also group by label to avoid merging segments with e.g. different faces or logos
    for group in sorted_df.group_by(["tdo_id", "signal", "label"], maintain_order=True):
        group_df = group[1].sort("start_s")
        rows = group_df.to_dicts()

        if not rows:
            continue

        # Start with the first segment as the current coalesced segment
        current_coalesced = rows[0].copy()

        for row in rows[1:]:
            # Check if this segment can be merged with the current coalesced segment
            if (
                tolerance_s is None
                or row["start_s"] <= current_coalesced["end_s"] + tolerance_s
            ):
                # Merge segments - extend the end time and take the max score
                current_coalesced = concat_segments(current_coalesced, row)

            else:
                # Gap is too large, save current coalesced segment and start a new one
                result_rows.append(current_coalesced)
                current_coalesced = row.copy()

        # Don't forget to add the last coalesced segment
        result_rows.append(current_coalesced)

    return new_segments_table(result_rows) if result_rows else new_segments_table([])


def segments_overlaps(df1: pl.DataFrame, df2: pl.DataFrame) -> pl.DataFrame:
    """Find segments from df1 that overlap with any segment in df2 (same tdo_id)."""
    if df1.is_empty() or df2.is_empty():
        return new_segments_table([])

    # Cross join on tdo_id and check overlap condition
    result = (
        df1.join(
            df2.select(["tdo_id", "start_s", "end_s"]).rename(
                {"start_s": "other_start_s", "end_s": "other_end_s"}
            ),
            on="tdo_id",
            how="inner",
        )
        .filter(
            # Overlap condition: not (end_s <= other_start_s or start_s >= other_end_s)
            ~(
                (pl.col("end_s") <= pl.col("other_start_s"))
                | (pl.col("start_s") >= pl.col("other_end_s"))
            )
        )
        .drop(["other_start_s", "other_end_s"])
        .unique()
    )

    return result


# table formatting for LLMs (token-friendly :))

_NUMERIC_DTYPES = (
    pl.Int8,
    pl.Int16,
    pl.Int32,
    pl.Int64,
    pl.UInt8,
    pl.UInt16,
    pl.UInt32,
    pl.UInt64,
    pl.Float32,
    pl.Float64,
)


def _is_numeric(dt) -> bool:
    return any(dt == t for t in _NUMERIC_DTYPES)


def _is_temporal(dt) -> bool:
    # Datetime and Duration are parametric types; use isinstance
    is_dt = False
    is_dur = False
    try:
        is_dt = isinstance(dt, pl.Datetime)
    except Exception:
        pass
    try:
        is_dur = isinstance(dt, pl.Duration)
    except Exception:
        pass
    return dt == pl.Date or dt == pl.Time or is_dt or is_dur


def _is_bool(dt) -> bool:
    return dt == pl.Boolean


def _is_stringy(dt) -> bool:
    # Plain Utf8 or categorical-ish types
    if dt == pl.Utf8:
        return True
    # Optional: treat Categorical/Enum as strings if available
    try:
        if isinstance(dt, pl.Categorical):
            return True
    except Exception:
        pass
    try:
        if isinstance(dt, pl.Enum):
            return True
    except Exception:
        pass
    return False


# ---- cell formatting helpers ----


def _sha8(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:8]


def _escape_cell(x) -> str:
    if x is None:
        return ""
    s = str(x)
    # keep rows single-line & delimiter-safe
    return (
        s.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def _truncate_text(x: str, limit: int | None) -> str:
    if x is None:
        return ""
    if limit is None or len(x) <= limit:
        return x
    return f"{x[:limit]}…(len={len(x)},sha1={_sha8(x)})"


# ---- main formatter ----


def format_table_delimited(
    df: pl.DataFrame,
    delimiter: str = "\t",  # TSV is compact; "|" also fine
    text_preview: int | None = 160,  # hard cap per text cell
    round_digits: int = 4,  # numeric rounding
    add_footer: bool = True,
    limit_rows: int = 50,  # final row cap
) -> str:
    if df is None or df.height == 0:
        return "(empty)\n"

    # Drop fully-null columns to save tokens
    keep_cols = [c for c in df.columns if df[c].null_count() < df.height]
    if not keep_cols:
        return "(no non-null columns)\n"
    df = df.select(keep_cols)

    casted = []
    for c in df.columns:
        s = df[c]
        dt = s.dtype

        if _is_stringy(dt):
            col = (
                s.cast(pl.Utf8)
                .map_elements(
                    lambda v: _escape_cell(_truncate_text(v, text_preview)),
                    return_dtype=pl.Utf8,
                )
                .alias(c)
            )
        elif _is_numeric(dt):
            # cast to float for compactness; round
            col = s.cast(pl.Float64).round(round_digits).alias(c)
        elif _is_temporal(dt) or _is_bool(dt):
            # stringify; escape to keep single line
            col = (
                s.cast(pl.Utf8)
                .map_elements(_escape_cell, return_dtype=pl.Utf8)
                .alias(c)
            )
        else:
            # lists/structs/decimal/etc -> stringify + escape + truncate
            col = (
                s.cast(pl.Utf8)
                .map_elements(
                    lambda v: _escape_cell(_truncate_text(v, text_preview)),
                    return_dtype=pl.Utf8,
                )
                .alias(c)
            )

        casted.append(col)

    df2 = pl.DataFrame(casted)

    # Row cap
    if df2.height > limit_rows:
        df_view = df2.head(limit_rows)
        remaining = df2.height - limit_rows
    else:
        df_view = df2
        remaining = 0

    # Header once, then rows
    header = delimiter.join(df_view.columns)
    rows = df_view.iter_rows()
    lines = [header] + [
        delimiter.join("" if v is None else str(v) for v in r) for r in rows
    ]

    if add_footer and remaining:
        lines.append(f"... +{remaining} more rows")

    return "\n".join(lines) + "\n"
