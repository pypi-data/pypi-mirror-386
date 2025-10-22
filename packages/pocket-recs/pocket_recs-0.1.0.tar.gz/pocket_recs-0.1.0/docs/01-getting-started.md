# Getting Started with Pocket-Recs

Welcome to **Pocket-Recs**, a CPU-only hybrid recommender system designed to bring enterprise-grade recommendations to small and medium businesses. This guide will help you get started in just a few minutes.

## What is Pocket-Recs?

Pocket-Recs is a production-ready recommendation engine that combines multiple strategies:

- **Two-tower retrieval** with ANN (FAISS/HNSW) for semantic search
- **Co-visitation** patterns with time decay
- **Brand-popularity** with recency weighting
- **LightGBM LambdaRank** for re-ranking
- **MMR diversification** to reduce redundancy

All components are **CPU-optimized** and require no GPU for training or inference.

## When to Use Pocket-Recs

### Perfect For:
- E-commerce shops with 100-100k products
- Content platforms (blogs, videos, music) with small-to-medium catalogs
- Startups wanting production-quality recommendations without ML infrastructure
- Cost-conscious teams ($5-25/month hosting)
- CPU-only environments (edge, serverless, modest VPS)

### Not Ideal For:
- Mega-scale catalogs (>1M items)
- Real-time personalization with <1ms latency requirements
- Cases where GPU acceleration is already available and preferred

## Quick Start (5 Minutes)

### 1. Install Pocket-Recs

```bash
# Recommended: Install with ANN support and API
pip install pocket-recs[ann,api]

# Or basic installation
pip install pocket-recs
```

**System Requirements:**
- Python 3.9 or higher
- 2-8 GB RAM (depending on catalog size)
- No GPU required (CPU-only)

### 2. Generate Sample Data

For this tutorial, we'll create sample data. Later, you can use your own.

```python
import polars as pl

# Create catalog
catalog = pl.DataFrame({
    "item_id": [f"item_{i}" for i in range(1, 101)],
    "brand": [f"Brand_{i%10}" for i in range(1, 101)],
    "category": [f"Category_{i%15}" for i in range(1, 101)],
    "title": [f"Product {i}" for i in range(1, 101)],
    "short_desc": [f"Description for product {i}" for i in range(1, 101)],
    "price": [10.0 + i * 2 for i in range(1, 101)],
    "in_stock": [True] * 100
})
catalog.write_csv("catalog.csv")

# Create interactions
import time
current_time = int(time.time() * 1000)

interactions = pl.DataFrame({
    "user_id": [f"user_{i%50:03d}" for i in range(1000)],
    "item_id": [f"item_{(i%100)+1}" for i in range(1000)],
    "brand": [f"Brand_{i%10}" for i in range(1000)],
    "timestamp": [current_time - (1000-i)*60000 for i in range(1000)],
    "event": ["view" if i%4!=0 else "purchase" for i in range(1000)],
    "quantity": [1] * 1000,
    "price": [10.0 + ((i%100)+1) * 2 for i in range(1000)]
})
interactions.write_parquet("interactions.parquet")
```

### 3. Train the Model

```bash
# Using CLI (easiest)
pocket-recs fit interactions.parquet catalog.csv artifacts/
```

Or using Python:

```python
from pocket_recs import fit

# Run offline training pipeline
artifacts_dir = fit(
    interactions_path="interactions.parquet",
    catalog_path="catalog.csv",
    out_dir="artifacts/"
)
print(f"Training complete! Artifacts saved to: {artifacts_dir}")
```

**What happens during training:**
- Sessionizes user interactions
- Builds co-visitation matrix
- Generates text embeddings for items
- Creates ANN index for fast similarity search
- Computes brand popularity scores
- Saves all artifacts for inference

**Training time:** ~30-60 seconds for 100 items

### 4. Get Recommendations

```python
from pocket_recs import Recommender
from pocket_recs.types import RecommendRequest, Interaction

# Load the recommender
recommender = Recommender(
    artifacts_dir="artifacts/",
    catalog_path="catalog.csv"
)

# Create a recommendation request
request = RecommendRequest(
    user_id="user_001",
    k=10,
    recent=[
        Interaction(
            user_id="user_001",
            item_id="item_5",
            timestamp=1700000000000,
            event="view"
        )
    ]
)

# Get recommendations
response = recommender.recommend(request)

# Display results
for item in response.items:
    print(f"{item.rank}. {item.item_id} (score: {item.score:.3f})")
    print(f"   Reasons: {', '.join(item.reasons)}")
```

**Expected output:**
```
1. item_42 (score: 0.847)
   Reasons: semantic, brand-popular
2. item_18 (score: 0.792)
   Reasons: brand-popular
3. item_23 (score: 0.765)
   Reasons: semantic
...
```

### 5. Start the API Server (Optional)

```bash
# Start FastAPI server
pocket-recs serve artifacts/ catalog.csv --port 8000
```

Then make API requests:

```bash
curl -X POST "http://localhost:8000/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "k": 10,
    "recent": [
      {
        "user_id": "user_001",
        "item_id": "item_5",
        "timestamp": 1700000000000,
        "event": "view"
      }
    ]
  }'
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Understanding the Results

Each recommendation includes:

| Field | Description |
|-------|-------------|
| `item_id` | Unique identifier for the product |
| `score` | Combined score from all strategies (higher = better) |
| `reasons` | List of why this item was recommended |
| `rank` | Position in the final ranked list (1 = best) |

### Reason Codes

| Code | Meaning |
|------|---------|
| `co-visited` | Users often view these items together |
| `brand-popular` | Popular item from relevant brand |
| `semantic` | Similar to user's viewed items |
| `baseline` | General popularity fallback |

## Next Steps

Now that you have the basics working, explore:

1. **[Core Concepts](02-core-concepts.md)** - Understand how Pocket-Recs works under the hood
2. **[Data Preparation](03-data-preparation.md)** - Learn about data formats and requirements
3. **[Configuration](07-configuration.md)** - Customize the recommender for your use case
4. **[API Guide](06-api-guide.md)** - Deploy as a REST API service
5. **[Production Deployment](09-production-deployment.md)** - Take it to production

## Common First Questions

### Do I need a GPU?
No! Pocket-Recs is designed to run entirely on CPU. Training and inference both work on modest hardware.

### What's the minimum amount of data needed?
- **Minimum**: 100+ items, 1000+ interactions, 50+ users
- **Recommended**: 1000+ items, 10k+ interactions, 500+ users
- More data = better recommendations!

### How often should I retrain?
- Small catalogs (<10k items): Daily or weekly
- Medium catalogs (10-50k): Weekly or bi-weekly
- Large catalogs (50k+): Weekly or monthly

### Can I use this for cold-start items?
Yes! New items with no interactions will still appear through semantic similarity (text embeddings) and brand popularity.

## Getting Help

- **Documentation**: Continue reading the docs in order
- **Issues**: [GitHub Issues](https://github.com/amjad/pocket-recs/issues)
- **Discussions**: [GitHub Discussions](https://github.com/amjad/pocket-recs/discussions)

---

**Ready to learn more?** Continue to [Core Concepts](02-core-concepts.md) to understand how Pocket-Recs works!

