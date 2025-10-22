"""
pocket-recs: CPU-only hybrid recommender system.

A research-proven, cost-efficient recommendation engine combining:
- Two-tower retrieval with ANN (FAISS/HNSW)
- Co-visitation and brand-popularity baselines
- LightGBM LambdaRank for re-ranking
- Optional cross-encoder reranking
- MMR diversification
"""

from pocket_recs.offline.fit import fit
from pocket_recs.online.recommender import Recommender

__version__ = "0.1.0"
__all__ = ["Recommender", "fit", "__version__"]

