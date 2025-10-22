"""ANN index building and querying (FAISS/HNSW)."""

from __future__ import annotations

from typing import Any, Tuple

import numpy as np


def build_ann_index(
    embeddings: np.ndarray, ef_construction: int = 200, M: int = 16
) -> Tuple[str, Any]:
    """
    Build ANN index using FAISS or hnswlib.

    Args:
        embeddings: Embedding matrix, shape (N, dim)
        ef_construction: HNSW ef_construction parameter
        M: HNSW M parameter (number of connections)

    Returns:
        Tuple of (backend_name, index_object)
    """
    if embeddings.shape[0] == 0:
        raise ValueError("Cannot build ANN index with zero embeddings")

    dim = embeddings.shape[1]
    n_elements = embeddings.shape[0]

    # Adjust parameters for small datasets
    if n_elements < 50:
        ef_construction = min(ef_construction, n_elements * 2)
        M = min(M, max(2, n_elements // 4))
        ef_query = min(64, n_elements)
    else:
        ef_query = 64

    try:
        import faiss

        index = faiss.IndexHNSWFlat(dim, M, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = ef_construction
        index.add(embeddings)
        return ("faiss", index)
    except ImportError:
        pass

    try:
        import hnswlib

        index = hnswlib.Index(space="ip", dim=dim)
        index.init_index(
            max_elements=n_elements, ef_construction=ef_construction, M=M
        )
        index.add_items(embeddings)
        index.set_ef(ef_query)
        return ("hnswlib", index)
    except ImportError:
        raise ImportError(
            "Neither faiss-cpu nor hnswlib is installed. "
            "Install with: pip install pocket-recs[ann]"
        )


def ann_query(
    index_tuple: Tuple[str, Any], query: np.ndarray, topk: int = 80
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Query ANN index for nearest neighbors.

    Args:
        index_tuple: (backend_name, index_object) from build_ann_index
        query: Query vectors, shape (n_queries, dim)
        topk: Number of neighbors to return

    Returns:
        Tuple of (indices, similarities), both shape (n_queries, topk)
    """
    backend, index = index_tuple

    if query.ndim == 1:
        query = query.reshape(1, -1)

    query = query.astype(np.float32)

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
        return indices, similarities
    elif backend == "hnswlib":
        indices, similarities = index.knn_query(query, k=effective_topk)
        # HNSWLib with inner product returns results in ascending order (most negative first)
        # We need to sort by similarity in descending order (highest similarity first)
        if query.shape[0] == 1:
            # Single query - sort the 1D results
            sorted_order = np.argsort(similarities[0])[::-1]
            return indices[0][sorted_order], similarities[0][sorted_order]
        else:
            # Batch queries - sort each query's results separately
            sorted_indices = np.zeros_like(indices)
            sorted_similarities = np.zeros_like(similarities)
            for i in range(query.shape[0]):
                sorted_order = np.argsort(similarities[i])[::-1]
                sorted_indices[i] = indices[i][sorted_order]
                sorted_similarities[i] = similarities[i][sorted_order]
            return sorted_indices, sorted_similarities
    else:
        raise ValueError(f"Unknown ANN backend: {backend}")


def save_ann_index(index_tuple: Tuple[str, Any], path: str) -> None:
    """
    Save ANN index to disk.

    Args:
        index_tuple: (backend_name, index_object)
        path: File path to save index
    """
    backend, index = index_tuple

    if backend == "faiss":
        import faiss

        faiss.write_index(index, path)
    elif backend == "hnswlib":
        index.save_index(path)
    else:
        raise ValueError(f"Unknown ANN backend: {backend}")


def load_ann_index(path: str, backend: str, dim: int) -> Tuple[str, Any]:
    """
    Load ANN index from disk.

    Args:
        path: File path to load index from
        backend: 'faiss' or 'hnswlib'
        dim: Embedding dimension

    Returns:
        Tuple of (backend_name, index_object)
    """
    if backend == "faiss":
        import faiss

        index = faiss.read_index(path)
        return ("faiss", index)
    elif backend == "hnswlib":
        import hnswlib

        index = hnswlib.Index(space="ip", dim=dim)
        index.load_index(path)
        return ("hnswlib", index)
    else:
        raise ValueError(f"Unknown ANN backend: {backend}")

