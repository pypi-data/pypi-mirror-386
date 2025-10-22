"""Configuration management for pocket-recs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EmbeddingConfig:
    """Configuration for text embeddings."""

    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 256
    normalize: bool = True
    device: str = "cpu"


@dataclass
class ANNConfig:
    """Configuration for ANN index."""

    ef_construction: int = 200
    M: int = 16
    ef_search: int = 64
    metric: str = "ip"


@dataclass
class CovisConfig:
    """Configuration for co-visitation."""

    top_k: int = 50
    tau_ms: int = 15 * 60_000
    session_gap_minutes: int = 30


@dataclass
class BrandPopConfig:
    """Configuration for brand-popularity."""

    half_life_days: int = 7
    top_n: int = 100


@dataclass
class RankerConfig:
    """Configuration for LightGBM ranker."""

    objective: str = "lambdarank"
    metric: str = "ndcg"
    ndcg_eval_at: list[int] | None = None
    num_leaves: int = 63
    learning_rate: float = 0.05
    min_data_in_leaf: int = 20
    num_boost_round: int = 500

    def __post_init__(self) -> None:
        if self.ndcg_eval_at is None:
            self.ndcg_eval_at = [10]


@dataclass
class MMRConfig:
    """Configuration for MMR diversification."""

    lambda_param: float = 0.7


@dataclass
class RecommenderConfig:
    """Master configuration for the recommender system."""

    embedding: EmbeddingConfig = EmbeddingConfig()
    ann: ANNConfig = ANNConfig()
    covis: CovisConfig = CovisConfig()
    brand_pop: BrandPopConfig = BrandPopConfig()
    ranker: RankerConfig = RankerConfig()
    mmr: MMRConfig = MMRConfig()

    candidate_sizes: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.candidate_sizes is None:
            self.candidate_sizes = {
                "covis": 40,
                "brand_pop": 40,
                "ann": 80,
                "item2vec": 40,
            }

