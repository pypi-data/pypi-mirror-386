"""Main recommender inference engine."""

from __future__ import annotations

import json
import os
import uuid
from typing import Dict, List, Optional, Set

import numpy as np
import polars as pl

from pocket_recs.config import RecommenderConfig
from pocket_recs.offline.index_ann import load_ann_index
from pocket_recs.offline.manifest import read_manifest
from pocket_recs.online.ann_utils import search_ann
from pocket_recs.online.mmr import mmr
from pocket_recs.online.reasons import generate_reason_codes
from pocket_recs.types import Interaction, RecommendItem, RecommendRequest, RecommendResponse


class Recommender:
    """
    Main recommender inference engine.

    Loads artifacts and serves recommendations using hybrid retrieval:
    - Co-visitation from recent interactions
    - Brand popularity
    - ANN semantic search
    - MMR diversification
    """

    def __init__(
        self,
        artifacts_dir: str,
        catalog_path: str,
        config: Optional[RecommenderConfig] = None,
    ):
        """
        Initialize recommender with artifacts.

        Args:
            artifacts_dir: Path to artifact directory
            catalog_path: Path to catalog CSV
            config: Optional recommender configuration
        """
        self.artifacts_dir = artifacts_dir
        self.catalog_path = catalog_path
        self.config = config or RecommenderConfig()

        self.manifest = read_manifest(artifacts_dir)

        self.catalog = pl.read_csv(catalog_path)
        self.item_index: Dict[str, int] = {
            str(item_id): idx for idx, item_id in enumerate(self.catalog["item_id"].to_list())
        }
        self.index_to_item: Dict[int, str] = {
            idx: str(item_id) for item_id, idx in self.item_index.items()
        }

        emb_path = os.path.join(artifacts_dir, self.manifest.emb_path)
        # Use memory mapping for large embeddings, regular loading for small ones
        # This helps avoid file locking issues in tests and small deployments
        embeddings = np.load(emb_path)
        if embeddings.nbytes < 50 * 1024 * 1024:  # Less than 50MB
            self.embeddings = embeddings
        else:
            self.embeddings = np.load(emb_path, mmap_mode="r")

        ann_path = os.path.join(artifacts_dir, self.manifest.ann_path)
        self.ann_index = load_ann_index(
            ann_path, self.manifest.ann_backend, self.manifest.embedding_dim
        )

        covis_path = os.path.join(artifacts_dir, self.manifest.covis_path)
        covis_data = np.load(covis_path, allow_pickle=True)
        self.covis_ids: Dict[str, np.ndarray] = covis_data["ids"].item()
        self.covis_weights: Dict[str, np.ndarray] = covis_data["weights"].item()
        covis_data.close()  # Explicitly close the npz file

        brandpop_path = os.path.join(artifacts_dir, self.manifest.brandpop_path)
        self.brand_pop = pl.read_parquet(brandpop_path)

    def _build_user_vector(
        self, recent_interactions: List[Interaction], k: int = 20
    ) -> Optional[np.ndarray]:
        """
        Build user vector from recent interactions.

        Args:
            recent_interactions: List of recent user interactions
            k: Number of recent items to consider

        Returns:
            User vector or None if no valid interactions
        """
        if not recent_interactions:
            return None

        vectors = []
        for interaction in recent_interactions[-k:]:
            idx = self.item_index.get(str(interaction.item_id))
            if idx is not None:
                vectors.append(self.embeddings[idx])

        if not vectors:
            return None

        user_vec = np.mean(np.stack(vectors, axis=0), axis=0)
        norm = np.linalg.norm(user_vec) + 1e-12
        return (user_vec / norm).astype(np.float32)

    def _get_covis_candidates(
        self, recent_interactions: List[Interaction], max_per_item: int = 50
    ) -> Set[int]:
        """Get co-visitation candidates from recent interactions."""
        candidates: Set[int] = set()

        for interaction in recent_interactions[-5:]:
            item_id_str = str(interaction.item_id)
            neighbor_ids = self.covis_ids.get(item_id_str)

            if neighbor_ids is not None:
                for neighbor_id in neighbor_ids[:max_per_item]:
                    neighbor_idx = self.item_index.get(str(neighbor_id))
                    if neighbor_idx is not None:
                        candidates.add(neighbor_idx)

        return candidates

    def _get_brand_pop_candidates(
        self, brand: Optional[str], max_items: int = 80
    ) -> Set[int]:
        """Get brand popularity candidates."""
        candidates: Set[int] = set()

        if brand:
            brand_items = (
                self.brand_pop.filter(pl.col("brand") == brand)
                .head(max_items)["item_id"]
                .to_list()
            )
        else:
            brand_items = self.brand_pop.head(max_items)["item_id"].to_list()

        for item_id in brand_items:
            idx = self.item_index.get(str(item_id))
            if idx is not None:
                candidates.add(idx)

        return candidates

    def _get_ann_candidates(
        self, user_vector: Optional[np.ndarray], topk: int = 80
    ) -> Dict[int, float]:
        """Get ANN candidates with similarity scores."""
        if user_vector is None:
            return {}

        indices, similarities = search_ann(self.ann_index, user_vector, topk=topk)

        return {int(idx): float(sim) for idx, sim in zip(indices, similarities)}

    def recommend(self, request: RecommendRequest) -> RecommendResponse:
        """
        Generate recommendations for a request.

        Args:
            request: Recommendation request

        Returns:
            Recommendation response with items and metadata
        """
        request_id = str(uuid.uuid4())

        user_vector = self._build_user_vector(request.recent)

        covis_candidates = self._get_covis_candidates(request.recent)
        brand_candidates = self._get_brand_pop_candidates(request.brand)
        ann_candidates_with_scores = self._get_ann_candidates(user_vector)

        all_candidates = (
            covis_candidates | brand_candidates | set(ann_candidates_with_scores.keys())
        )

        if request.exclusions:
            exclusion_indices = {
                self.item_index.get(str(item_id))
                for item_id in request.exclusions
                if self.item_index.get(str(item_id)) is not None
            }
            all_candidates -= exclusion_indices

        if not all_candidates:
            fallback_items = self.brand_pop.head(request.k)["item_id"].to_list()
            items = [
                RecommendItem(
                    item_id=str(item_id),
                    score=0.0,
                    reasons=["baseline"],
                    rank=rank + 1,
                )
                for rank, item_id in enumerate(fallback_items)
            ]
            return RecommendResponse(
                request_id=request_id,
                items=items,
                artifact_version=self.manifest.version,
            )

        candidate_array = np.array(list(all_candidates), dtype=np.int32)

        scores = np.zeros(len(candidate_array), dtype=np.float32)
        has_covis = np.zeros(len(candidate_array), dtype=bool)
        brand_boosts = np.zeros(len(candidate_array), dtype=np.float32)

        for j, idx in enumerate(candidate_array):
            if idx in covis_candidates:
                has_covis[j] = True
                scores[j] += 0.3

            if idx in brand_candidates:
                brand_boosts[j] = 0.15
                scores[j] += 0.15

            ann_score = ann_candidates_with_scores.get(int(idx), 0.0)
            scores[j] += ann_score

        candidate_embeddings = self.embeddings[candidate_array]
        similarity_matrix = (candidate_embeddings @ candidate_embeddings.T).astype(np.float32)

        selected_indices = mmr(
            candidate_indices=candidate_array,
            similarity_matrix=similarity_matrix,
            scores=scores,
            k=request.k,
            lambda_param=self.config.mmr.lambda_param,
        )

        items: List[RecommendItem] = []
        for rank, idx in enumerate(selected_indices, start=1):
            item_id = self.index_to_item[idx]
            cand_pos = np.where(candidate_array == idx)[0][0]

            reason_codes = generate_reason_codes(
                has_covis=bool(has_covis[cand_pos]),
                ann_score=ann_candidates_with_scores.get(idx, 0.0),
                brand_boost=float(brand_boosts[cand_pos]),
            )

            items.append(
                RecommendItem(
                    item_id=item_id,
                    score=float(scores[cand_pos]),
                    reasons=reason_codes,
                    rank=rank,
                )
            )

        return RecommendResponse(
            request_id=request_id,
            items=items,
            artifact_version=self.manifest.version,
            metadata={
                "total_candidates": len(all_candidates),
                "covis_candidates": len(covis_candidates),
                "brand_candidates": len(brand_candidates),
                "ann_candidates": len(ann_candidates_with_scores),
            },
        )

    def close(self) -> None:
        """Clean up resources to avoid file locking issues."""
        # If embeddings is a memory-mapped array, it doesn't need explicit cleanup
        # If it's a regular array, it will be garbage collected automatically
        # But we can help by clearing the reference
        if hasattr(self, 'embeddings'):
            self.embeddings = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
        return False  # Don't suppress exceptions

