"""Maximal Marginal Relevance (MMR) diversification."""

from __future__ import annotations

from typing import List

import numpy as np


def mmr(
    candidate_indices: np.ndarray,
    similarity_matrix: np.ndarray,
    scores: np.ndarray,
    k: int,
    lambda_param: float = 0.7,
) -> List[int]:
    """
    Apply MMR diversification to candidate set.

    Args:
        candidate_indices: Array of candidate item indices
        similarity_matrix: Pairwise similarity matrix (cand x cand)
        scores: Relevance scores for candidates
        k: Number of items to select
        lambda_param: Trade-off between relevance and diversity (0-1)

    Returns:
        List of selected item indices in order
    """
    if len(candidate_indices) == 0:
        return []

    if len(candidate_indices) <= k:
        return candidate_indices.tolist()

    selected_positions: List[int] = []
    remaining_positions = list(range(len(candidate_indices)))

    while remaining_positions and len(selected_positions) < k:
        if not selected_positions:
            # For the first item, select the one with highest relevance (greedy)
            best_pos = remaining_positions[np.argmax([scores[pos] for pos in remaining_positions])]
        else:
            # For subsequent items, use full MMR calculation
            best_pos = None
            best_value = -np.inf

            for pos in remaining_positions:
                relevance = scores[pos]
                max_sim = max(
                    similarity_matrix[pos, selected_pos]
                    for selected_pos in selected_positions
                )
                diversity = 1.0 - max_sim
                mmr_value = lambda_param * relevance + (1 - lambda_param) * diversity

                if mmr_value > best_value:
                    best_value = mmr_value
                    best_pos = pos

        if best_pos is not None:
            selected_positions.append(best_pos)
            remaining_positions.remove(best_pos)

    # Debug output
    result = [int(candidate_indices[pos]) for pos in selected_positions]
    print(f"DEBUG: selected_positions={selected_positions}, result={result}")
    return result

