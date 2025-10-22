"""Sessionization logic for user interactions."""

from __future__ import annotations

import polars as pl


def sessionize(df: pl.DataFrame, gap_minutes: int = 30) -> pl.DataFrame:
    """
    Sessionize user interactions based on time gaps.

    Args:
        df: DataFrame with user_id, timestamp columns
        gap_minutes: Maximum gap between interactions in same session

    Returns:
        DataFrame with added session_id column
    """
    if df.is_empty():
        return df.with_columns(pl.lit(0).alias("session_id"))

    gap_ms = gap_minutes * 60_000

    df_sorted = df.sort(["user_id", "timestamp"])

    df_with_prev = df_sorted.with_columns(
        [pl.col("timestamp").shift().over("user_id").alias("prev_ts")]
    )

    df_sessionized = df_with_prev.with_columns(
        [
            (
                (pl.col("prev_ts").is_null())
                | ((pl.col("timestamp") - pl.col("prev_ts")) > gap_ms)
            )
            .cast(pl.Int32)
            .cum_sum()
            .over("user_id")
            .alias("session_id")
        ]
    ).drop("prev_ts")

    return df_sessionized

