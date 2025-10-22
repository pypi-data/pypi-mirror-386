"""Brand-recency popularity scoring."""

from __future__ import annotations

import time

import numpy as np
import polars as pl


def build_brand_pop(
    df: pl.DataFrame, half_life_days: int = 7, topn: int = 100
) -> pl.DataFrame:
    """
    Build brand-popularity scores with recency decay.

    Args:
        df: DataFrame with brand, category, item_id, timestamp, event
        half_life_days: Half-life for exponential time decay
        topn: Top N items to keep per brand-category

    Returns:
        DataFrame with brand, category, item_id, score sorted by score
    """
    if df.is_empty():
        return pl.DataFrame(
            schema={
                "brand": pl.Utf8,
                "category": pl.Utf8,
                "item_id": pl.Utf8,
                "score": pl.Float64,
            }
        )

    now_ms = int(time.time() * 1000)
    lambda_decay = np.log(2) / (half_life_days * 86400000)
    event_weights = {"view": 1.0, "add": 2.0, "purchase": 3.0}

    brand_pop_df = (
        df.with_columns(
            [
                (pl.lit(now_ms) - pl.col("timestamp"))
                .map_elements(
                    lambda d: float(np.exp(-lambda_decay * float(d))),
                    return_dtype=pl.Float64,
                )
                .alias("decay"),
                pl.col("event").replace_strict(event_weights).alias("w_evt"),
            ]
        )
        .with_columns([(pl.col("decay") * pl.col("w_evt")).alias("score")])
        .group_by(["brand", "category", "item_id"])
        .agg(pl.col("score").sum())
        .sort(["brand", "category", "score"], descending=[False, False, True])
    )

    result_parts = []
    for group in brand_pop_df.partition_by(["brand", "category"], as_dict=False):
        result_parts.append(group.head(topn))

    if result_parts:
        return pl.concat(result_parts)
    else:
        return pl.DataFrame(
            schema={
                "brand": pl.Utf8,
                "category": pl.Utf8,
                "item_id": pl.Utf8,
                "score": pl.Float64,
            }
        )

