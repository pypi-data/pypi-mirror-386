"""ANN search utilities for online inference."""

from __future__ import annotations

from typing import Any, Tuple

import numpy as np


def search_ann(
    index_tuple: Tuple[str, Any], user_vector: np.ndarray, topk: int = 80
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Search ANN index with user vector.

    Args:
        index_tuple: (backend_name, index_object)
        user_vector: User embedding vector, shape (dim,) or (1, dim)
        topk: Number of nearest neighbors

    Returns:
        Tuple of (indices, similarities)
    """
    if user_vector.ndim == 1:
        query = user_vector.reshape(1, -1).astype(np.float32)
    else:
        query = user_vector.astype(np.float32)

    backend, index = index_tuple

    # Get the actual size of the index to avoid requesting more results than available
    if backend == "faiss":
        actual_size = index.ntotal
    elif backend == "hnswlib":
        actual_size = index.get_current_count()
    else:
        actual_size = float('inf')  # Unknown backend, assume large

    # Don't request more results than the index contains
    effective_topk = min(topk, actual_size)

    if backend == "faiss":
        similarities, indices = index.search(query, effective_topk)
        return indices[0], similarities[0]
    elif backend == "hnswlib":
        indices, similarities = index.knn_query(query, k=effective_topk)
        # HNSWLib with inner product returns results in ascending order (most negative first)
        # We need to sort by similarity in descending order (highest similarity first)
        sorted_order = np.argsort(similarities[0])[::-1]  # Sort descending
        return indices[0][sorted_order], similarities[0][sorted_order]
    else:
        raise ValueError(f"Unknown ANN backend: {backend}")

