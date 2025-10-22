# Offline Training

This guide covers the offline training pipeline, which builds all the artifacts needed for fast online inference.

## Overview

The offline training pipeline takes your catalog and interactions data and produces:

- **Embeddings**: Vector representations of items
- **ANN Index**: Fast similarity search structure
- **Co-visitation Matrix**: Item-to-item patterns
- **Brand Popularity**: Trending items per brand
- **Manifest**: Metadata about the trained model

## Quick Start

### Using CLI

```bash
pocket-recs fit interactions.parquet catalog.csv artifacts/
```

### Using Python API

```python
from pocket_recs import fit

artifacts_dir = fit(
    interactions_path="interactions.parquet",
    catalog_path="catalog.csv",
    out_dir="artifacts/"
)

print(f"Training complete! Artifacts saved to: {artifacts_dir}")
```

## Training Pipeline Steps

### Step 1: Data Loading

**What happens**:
- Loads interactions from Parquet file
- Loads catalog from CSV file
- Validates data formats
- Checks for missing items

**Requirements**:
- Interactions must have: user_id, item_id, timestamp, event
- Catalog must have: item_id, title
- Timestamps must be in milliseconds

### Step 2: Sessionization

**What happens**:
- Groups interactions by user
- Splits into sessions based on time gaps
- Default session gap: 30 minutes

**Output**: Session-aware interaction data

**Configuration**:
```python
from pocket_recs.config import RecommenderConfig, CovisConfig

config = RecommenderConfig(
    covis=CovisConfig(
        session_gap_minutes=30  # Adjust session boundary
    )
)

artifacts_dir = fit(
    interactions_path="interactions.parquet",
    catalog_path="catalog.csv",
    out_dir="artifacts/",
    config=config
)
```

### Step 3: Co-visitation Matrix

**What happens**:
- Analyzes items viewed together in sessions
- Applies time decay: closer in time = stronger relationship
- Builds sparse matrix of item-to-item similarities
- Keeps top-K most related items per item

**Output**: `covis.npz` (sparse matrix in NumPy format)

**Configuration**:
```python
config = RecommenderConfig(
    covis=CovisConfig(
        top_k=50,              # Items per seed item
        tau_ms=900000,         # 15 minutes time decay
        session_gap_minutes=30 # Session boundary
    )
)
```

**Performance**:
- 10K items: ~5 seconds
- 50K items: ~30 seconds
- 100K items: ~2 minutes

### Step 4: Brand Popularity

**What happens**:
- Counts interactions per brand-item pair
- Applies exponential time decay (recent = more important)
- Ranks items within each brand
- Keeps top-N items per brand

**Output**: `brand_pop.parquet` (brand-item popularity scores)

**Configuration**:
```python
from pocket_recs.config import BrandPopConfig

config = RecommenderConfig(
    brand_pop=BrandPopConfig(
        half_life_days=7,  # How fast popularity decays
        top_n=100         # Items per brand to keep
    )
)
```

**Performance**:
- 10K items: ~2 seconds
- 50K items: ~10 seconds
- 100K items: ~30 seconds

### Step 5: Text Embeddings

**What happens**:
- Combines item text fields: title + brand + category + description
- Encodes text using sentence-transformers model
- Generates dense vectors (e.g., 384 dimensions)
- L2-normalizes vectors for cosine similarity

**Output**: `embeddings.npy` (NumPy array of shape [N_items, embedding_dim])

**Configuration**:
```python
from pocket_recs.config import EmbeddingConfig

config = RecommenderConfig(
    embedding=EmbeddingConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",  # Model choice
        batch_size=256,      # Batch size for encoding
        normalize=True,      # L2 normalize embeddings
        device="cpu"         # "cpu" or "cuda"
    )
)
```

**Performance** (CPU):
- 10K items: ~2-3 minutes
- 50K items: ~10-15 minutes
- 100K items: ~30-45 minutes

**Model Options**:

| Model | Dimensions | Speed | Quality | Best For |
|-------|------------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | Fastest | Good | Production (default) |
| `all-MiniLM-L12-v2` | 384 | Fast | Better | Balance |
| `all-mpnet-base-v2` | 768 | Slow | Best | High quality |
| `paraphrase-MiniLM-L3-v2` | 384 | Very Fast | Okay | Low latency |

### Step 6: ANN Index

**What happens**:
- Builds HNSW (Hierarchical Navigable Small World) graph
- Creates index for fast approximate nearest neighbor search
- Optimizes for query-time performance

**Output**: `ann_index.bin` (HNSW index file)

**Configuration**:
```python
from pocket_recs.config import ANNConfig

config = RecommenderConfig(
    ann=ANNConfig(
        backend="hnswlib",    # "hnswlib" or "faiss"
        M=16,                 # Graph connectivity
        ef_construction=200,  # Build quality
        ef_search=64,         # Query quality
        metric="ip"           # "ip" (inner product) or "l2"
    )
)
```

**Parameters Explained**:

| Parameter | Effect | Trade-off |
|-----------|--------|-----------|
| `M` | Graph connectivity | Higher = better recall, more memory |
| `ef_construction` | Build-time search | Higher = better index, slower build |
| `ef_search` | Query-time search | Higher = better recall, slower queries |

**Performance**:
- 10K items: ~5 seconds
- 50K items: ~30 seconds
- 100K items: ~2 minutes

### Step 7: Manifest

**What happens**:
- Records training metadata
- Saves configuration used
- Timestamps artifact creation
- Enables version tracking

**Output**: `manifest.json`

**Example**:
```json
{
  "version": "0.1.0",
  "created_at": "2024-10-19T10:30:00",
  "config": {
    "embedding": {
      "model_name": "sentence-transformers/all-MiniLM-L6-v2",
      "embedding_dim": 384
    },
    "ann": {
      "backend": "hnswlib",
      "M": 16,
      "ef_construction": 200
    }
  },
  "stats": {
    "num_items": 10000,
    "num_interactions": 50000,
    "num_users": 5000
  }
}
```

## Complete Training Example

```python
from pocket_recs import fit
from pocket_recs.config import (
    RecommenderConfig,
    EmbeddingConfig,
    ANNConfig,
    CovisConfig,
    BrandPopConfig,
)

# Configure all components
config = RecommenderConfig(
    embedding=EmbeddingConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        batch_size=256,
        normalize=True,
        device="cpu",
    ),
    ann=ANNConfig(
        backend="hnswlib",
        M=16,
        ef_construction=200,
        ef_search=64,
        metric="ip",
    ),
    covis=CovisConfig(
        top_k=50,
        tau_ms=900000,  # 15 minutes
        session_gap_minutes=30,
    ),
    brand_pop=BrandPopConfig(
        half_life_days=7,
        top_n=100,
    ),
)

# Run training
artifacts_dir = fit(
    interactions_path="data/interactions.parquet",
    catalog_path="data/catalog.csv",
    out_dir="artifacts/v1",
    config=config
)

print(f"Training complete!")
print(f"Artifacts: {artifacts_dir}")
```

## Artifacts Directory Structure

After training, your artifacts directory will contain:

```
artifacts/
├── embeddings.npy          # Item embeddings [N_items, embedding_dim]
├── ann_index.bin           # HNSW index for similarity search
├── covis.npz              # Co-visitation matrix (sparse)
├── brand_pop.parquet      # Brand popularity scores
└── manifest.json          # Training metadata
```

## Training Performance

### Benchmarks (2 vCPU / 4-8 GB RAM, CPU-only)

| Catalog Size | Interactions | Training Time | Artifact Size |
|--------------|-------------|---------------|---------------|
| 1K items | 5K | 1-2 min | ~5 MB |
| 10K items | 50K | 5-10 min | ~50 MB |
| 50K items | 250K | 15-30 min | ~250 MB |
| 100K items | 500K | 30-60 min | ~500 MB |

### Memory Requirements

| Catalog Size | Peak Memory | Recommended RAM |
|--------------|-------------|-----------------|
| 10K items | ~1 GB | 2 GB |
| 50K items | ~2 GB | 4 GB |
| 100K items | ~4 GB | 6-8 GB |

## Optimization Tips

### 1. Faster Training

**Use smaller embedding model**:
```python
config.embedding.model_name = "sentence-transformers/paraphrase-MiniLM-L3-v2"
```

**Increase batch size** (if you have RAM):
```python
config.embedding.batch_size = 512
```

**Reduce ANN index quality**:
```python
config.ann.ef_construction = 100  # Faster build, slightly worse quality
config.ann.M = 12
```

### 2. Better Quality

**Use better embedding model**:
```python
config.embedding.model_name = "sentence-transformers/all-mpnet-base-v2"
```

**Increase ANN index quality**:
```python
config.ann.ef_construction = 400
config.ann.M = 32
```

**Keep more co-visitation candidates**:
```python
config.covis.top_k = 100
```

### 3. Large Catalogs (>100K items)

**Use FAISS instead of HNSW**:
```python
config.ann.backend = "faiss"
config.ann.index_type = "IVF"
config.ann.nlist = 1000  # Number of clusters
```

**Use quantization** (coming soon):
```python
config.ann.use_quantization = True
```

## Incremental Updates

For production systems, you may want to retrain regularly:

### Strategy 1: Full Retrain (Recommended)

```python
# Retrain from scratch weekly
artifacts_dir = fit(
    interactions_path="interactions_last_90_days.parquet",
    catalog_path="catalog.csv",
    out_dir=f"artifacts/v{version}",
    config=config
)
```

**Pros**: Clean, reproducible, handles catalog changes  
**Cons**: Slower for very large catalogs

### Strategy 2: Hot Swap

```python
import shutil
from datetime import datetime

# Train to temporary directory
temp_dir = "artifacts/temp"
artifacts_dir = fit(
    interactions_path="interactions.parquet",
    catalog_path="catalog.csv",
    out_dir=temp_dir,
    config=config
)

# Backup old artifacts
backup_dir = f"artifacts/backup_{datetime.now().isoformat()}"
shutil.move("artifacts/current", backup_dir)

# Swap in new artifacts
shutil.move(temp_dir, "artifacts/current")

# Restart inference service
# (service will reload from "artifacts/current")
```

### Strategy 3: A/B Testing

```python
# Train two versions with different configs
artifacts_v1 = fit(..., out_dir="artifacts/v1", config=config_v1)
artifacts_v2 = fit(..., out_dir="artifacts/v2", config=config_v2)

# Load both recommenders
from pocket_recs import Recommender

recommender_v1 = Recommender(artifacts_dir="artifacts/v1", catalog_path="catalog.csv")
recommender_v2 = Recommender(artifacts_dir="artifacts/v2", catalog_path="catalog.csv")

# Route traffic based on user_id
def get_recommender(user_id: str):
    return recommender_v1 if hash(user_id) % 2 == 0 else recommender_v2
```

## Monitoring Training

### Basic Progress Logging

```python
import logging

logging.basicConfig(level=logging.INFO)

artifacts_dir = fit(
    interactions_path="interactions.parquet",
    catalog_path="catalog.csv",
    out_dir="artifacts/",
    config=config
)
```

### Custom Progress Tracking (Advanced)

```python
from pocket_recs.offline import (
    sessionize,
    build_covis,
    build_brand_pop,
    generate_embeddings,
    build_ann_index,
)
import time

def fit_with_progress(interactions_path, catalog_path, out_dir, config):
    """Train with detailed progress tracking."""
    
    start_time = time.time()
    
    print("Step 1/5: Sessionizing...")
    step_start = time.time()
    sessions = sessionize(interactions_path, config)
    print(f"  Done in {time.time() - step_start:.1f}s")
    
    print("Step 2/5: Building co-visitation...")
    step_start = time.time()
    covis = build_covis(sessions, config)
    print(f"  Done in {time.time() - step_start:.1f}s")
    
    print("Step 3/5: Computing brand popularity...")
    step_start = time.time()
    brand_pop = build_brand_pop(interactions_path, config)
    print(f"  Done in {time.time() - step_start:.1f}s")
    
    print("Step 4/5: Generating embeddings...")
    step_start = time.time()
    embeddings = generate_embeddings(catalog_path, config)
    print(f"  Done in {time.time() - step_start:.1f}s")
    print(f"  Embedding shape: {embeddings.shape}")
    
    print("Step 5/5: Building ANN index...")
    step_start = time.time()
    index = build_ann_index(embeddings, config)
    print(f"  Done in {time.time() - step_start:.1f}s")
    
    # Save artifacts
    # ... (save logic)
    
    total_time = time.time() - start_time
    print(f"\nTotal training time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    
    return out_dir
```

## Troubleshooting

### Out of Memory

**Symptoms**: Process killed, "Killed" message, OOM errors

**Solutions**:

1. **Reduce batch size**:
```python
config.embedding.batch_size = 64  # or 32
```

2. **Use smaller model**:
```python
config.embedding.model_name = "sentence-transformers/paraphrase-MiniLM-L3-v2"
```

3. **Process in chunks** (for very large catalogs):
```python
# Split catalog into chunks
chunk_size = 10000
for i in range(0, len(catalog), chunk_size):
    chunk = catalog[i:i+chunk_size]
    embeddings_chunk = generate_embeddings(chunk, config)
    # ... save chunk
```

### Slow Training

**Symptoms**: Training takes >2 hours for 50K items

**Solutions**:

1. **Use faster embedding model**
2. **Reduce ef_construction**
3. **Filter old interactions** (keep last 90 days)
4. **Check for disk I/O bottlenecks**

### Poor Recommendation Quality

**Symptoms**: Random-looking recommendations

**Solutions**:

1. **Check data quality** (see Data Preparation guide)
2. **Use better embedding model**
3. **Increase training data** (more interactions)
4. **Tune configuration** (see Configuration guide)

## Next Steps

- **[Online Recommendations](05-online-recommendations.md)**: Use trained model for inference
- **[Configuration](07-configuration.md)**: Deep dive into all config options
- **[Production Deployment](09-production-deployment.md)**: Deploy to production

---

Training is a one-time cost that enables fast, high-quality recommendations at inference time!

