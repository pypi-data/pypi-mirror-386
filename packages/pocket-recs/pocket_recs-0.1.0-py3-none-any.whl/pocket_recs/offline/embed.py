"""Text embedding generation using sentence transformers."""

from __future__ import annotations

from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


def build_item_embeddings(
    texts: List[str],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    batch_size: int = 256,
    normalize: bool = True,
    device: str = "cpu",
) -> np.ndarray:
    """
    Generate text embeddings for catalog items.

    Args:
        texts: List of text strings to embed
        model_name: Sentence transformer model name
        batch_size: Batch size for encoding
        normalize: Whether to L2 normalize embeddings
        device: Device to use ('cpu' or 'cuda')

    Returns:
        Array of embeddings, shape (N, embedding_dim)
    """
    if not texts:
        return np.array([], dtype=np.float32).reshape(0, 384)

    model = SentenceTransformer(model_name, device=device)

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
        show_progress_bar=True,
    )

    return embeddings.astype(np.float32)

