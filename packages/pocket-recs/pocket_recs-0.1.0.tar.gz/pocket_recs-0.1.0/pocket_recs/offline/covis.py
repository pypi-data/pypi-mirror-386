"""Co-visitation matrix computation with time decay."""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import polars as pl


def build_covis(
    df_sess: pl.DataFrame, k: int = 50, tau_ms: int = 15 * 60_000
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    Build co-visitation matrix from sessionized interactions.

    Args:
        df_sess: DataFrame with session_id, item_id, timestamp, event
        k: Top-K neighbors to keep per item
        tau_ms: Time decay parameter in milliseconds

    Returns:
        Dictionary mapping item_id to (neighbor_ids, weights)
    """
    if df_sess.is_empty():
        return {}

    event_weights = {"view": 1.0, "add": 2.0, "purchase": 3.0}

    df_prepared = df_sess.select(["session_id", "item_id", "timestamp", "event"])

    pairs = (
        df_prepared.join(df_prepared, on="session_id", suffix="_j")
        .filter(pl.col("item_id") != pl.col("item_id_j"))
        .with_columns(
            [
                (pl.col("timestamp_j") - pl.col("timestamp")).abs().alias("dt"),
                pl.col("event").replace_strict(event_weights).alias("w_i"),
                pl.col("event_j").replace_strict(event_weights).alias("w_j"),
            ]
        )
        .with_columns(
            [
                (
                    pl.col("w_i")
                    * pl.col("w_j")
                    * pl.col("dt").map_elements(
                        lambda d: int(np.exp(-float(d) / tau_ms) * 1_000_000),
                        return_dtype=pl.Int64,
                    )
                ).alias("w")
            ]
        )
        .group_by(["item_id", "item_id_j"])
        .agg(pl.col("w").sum())
        .rename({"item_id_j": "nbr", "w": "weight"})
    )

    covis_dict: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

    item_groups = pairs.partition_by("item_id", as_dict=True)
    for item_id, group in item_groups.items():
        sorted_group = group.sort("weight", descending=True).head(k)
        nbr_array = sorted_group["nbr"].to_numpy()
        weight_array = sorted_group["weight"].to_numpy().astype(np.float32)
        covis_dict[str(item_id)] = (nbr_array, weight_array)

    return covis_dict

