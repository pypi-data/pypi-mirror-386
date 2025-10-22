"""LightGBM LambdaRank training."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import lightgbm as lgb
import numpy as np


def train_lambdarank(
    X: np.ndarray,
    y: np.ndarray,
    group: np.ndarray,
    params: Optional[Dict[str, Any]] = None,
    num_boost_round: int = 500,
    X_val: Optional[np.ndarray] = None,
    y_val: Optional[np.ndarray] = None,
    group_val: Optional[np.ndarray] = None,
) -> lgb.Booster:
    """
    Train LightGBM LambdaRank model.

    Args:
        X: Training features, shape (n_samples, n_features)
        y: Training labels (relevance scores), shape (n_samples,)
        group: Group sizes for queries, shape (n_groups,)
        params: LightGBM parameters (optional)
        num_boost_round: Number of boosting rounds
        X_val: Validation features (optional)
        y_val: Validation labels (optional)
        group_val: Validation group sizes (optional)

    Returns:
        Trained LightGBM booster
    """
    if params is None:
        params = {
            "objective": "lambdarank",
            "metric": "ndcg",
            "ndcg_eval_at": [10, 20],
            "num_leaves": 63,
            "learning_rate": 0.05,
            "min_data_in_leaf": 20,
            "verbose": -1,
            "force_row_wise": True,
        }

    train_data = lgb.Dataset(X, label=y, group=group)

    valid_sets: Optional[List[lgb.Dataset]] = None
    if X_val is not None and y_val is not None and group_val is not None:
        val_data = lgb.Dataset(X_val, label=y_val, group=group_val, reference=train_data)
        valid_sets = [train_data, val_data]

    booster = lgb.train(
        params,
        train_data,
        num_boost_round=num_boost_round,
        valid_sets=valid_sets,
        valid_names=["train", "valid"] if valid_sets else None,
    )

    return booster

