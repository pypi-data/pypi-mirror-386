import polars as pl
from typing import Optional, Literal

from veri_agents_aiware.content_intelligence.ops import ConstraintRelation


# Expected schema columns in both DataFrames:
#   tdo_id (Utf8), start_s (Float64), end_s (Float64)
# Plus whatever other columns you keep (label, signal, etc.)


def _relation_filter_expr(
    rel: ConstraintRelation,
    within_s: Optional[float],
    tol: float,
) -> pl.Expr:
    """
    Returns a Polars boolean expression using left/right columns:
      start_s, end_s, start_s_right, end_s_right
    """
    l_start = pl.col("start_s")
    l_end = pl.col("end_s")
    r_start = pl.col("start_s_right")
    r_end = pl.col("end_s_right")

    if rel == "BEFORE":
        # a.end <= b.start + tol AND (gap <= within+tol if within set)
        base = l_end <= r_start + tol
        if within_s is not None:
            base = base & ((r_start - l_end) <= (within_s + tol))
        return base

    if rel == "AFTER":
        # a starts after b ends (mirror of BEFORE)
        base = r_end <= l_start + tol
        if within_s is not None:
            base = base & ((l_start - r_end) <= (within_s + tol))
        return base

    if rel == "OVERLAPS":
        # (a.start < b.end + tol) AND (b.start < a.end + tol)
        return (l_start < r_end + tol) & (r_start < l_end + tol)

    if rel == "WITHIN":
        # a fully inside b (ignore within_s)
        return (l_start >= r_start - tol) & (l_end <= r_end + tol)

    raise ValueError(f"Unknown relation: {rel}")


def join_temporal(
    left: pl.DataFrame,
    right: pl.DataFrame,
    *,
    relation: ConstraintRelation,
    within_s: Optional[float] = None,
    tol: float = 0.0,
    how: Literal["pairs", "semi"] = "pairs",
    suffix_right: str = "_right",
) -> pl.DataFrame:
    """
    Temporal join between two segment tables scoped by tdo_id.
    - relation: BEFORE | AFTER | OVERLAPS | WITHIN
    - within_s: optional proximity bound for BEFORE/AFTER
    - tol: boundary softness (>=0)
    - how:
        "pairs" -> return matched pairs with left/right columns
        "semi"  -> return unique left rows that matched at least one right

    Any extra columns are preserved (right columns get suffix).
    """

    L = left.lazy()
    R = right.lazy()

    # Inner join on tdo_id to avoid cross-TDO pairings
    # (Polars keeps the left/right columns; right cols will be suffixed)
    joined = L.join(
        R,
        on="tdo_id",
        how="inner",
        suffix=suffix_right,  # for overlapping non-time columns
    ).filter(_relation_filter_expr(relation, within_s, tol))

    if how == "pairs":
        return joined.collect()

    if how == "semi":
        # Keep only distinct left rows that matched
        left_cols = [c for c in L.collect_schema().names()]
        # The join renamed times to *_left; fix that back for the output.
        result = (
            joined.select(left_cols)  # drop right-side columns
            .unique()  # distinct left rows
        )
        return result.collect()

    raise ValueError(f"Unknown how: {how}")
