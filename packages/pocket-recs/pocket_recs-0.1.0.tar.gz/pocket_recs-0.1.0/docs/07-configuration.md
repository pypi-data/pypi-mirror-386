# Configuration Guide

This comprehensive guide covers all configuration options in Pocket-Recs for tuning performance, quality, and behavior.

## Overview

Pocket-Recs uses a hierarchical configuration system with these main components:

- **EmbeddingConfig**: Text-to-vector conversion
- **ANNConfig**: Approximate nearest neighbor search
- **CovisConfig**: Co-visitation patterns
- **BrandPopConfig**: Brand popularity
- **RankerConfig**: Learning-to-rank (optional)
- **MMRConfig**: Diversification
- **CandidateSizes**: Candidate pool sizes

## Configuration Structure

```python
from pocket_recs.config import (
    RecommenderConfig,
    EmbeddingConfig,
    ANNConfig,
    CovisConfig,
    BrandPopConfig,
    MMRConfig,
)

config = RecommenderConfig(
    embedding=EmbeddingConfig(...),
    ann=ANNConfig(...),
    covis=CovisConfig(...),
    brand_pop=BrandPopConfig(...),
    mmr=MMRConfig(...),
    candidate_sizes={...},
)
```

## Embedding Configuration

Controls how text is converted to vectors.

```python
from pocket_recs.config import EmbeddingConfig

embedding_config = EmbeddingConfig(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    batch_size=256,
    normalize=True,
    device="cpu",
    max_length=512,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | str | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `batch_size` | int | 256 | Batch size for encoding |
| `normalize` | bool | True | L2-normalize embeddings |
| `device` | str | `cpu` | Device: "cpu" or "cuda" |
| `max_length` | int | 512 | Maximum sequence length |

### Model Options

| Model | Dimensions | Speed | Quality | Use Case |
|-------|------------|-------|---------|----------|
| `paraphrase-MiniLM-L3-v2` | 384 | Fastest | Good | Low latency |
| `all-MiniLM-L6-v2` | 384 | Fast | Better | **Default** |
| `all-MiniLM-L12-v2` | 384 | Medium | Good | Balanced |
| `all-mpnet-base-v2` | 768 | Slow | Best | High quality |
| `multi-qa-mpnet-base-dot-v1` | 768 | Slow | Best | Q&A/semantic search |

### Performance vs Quality Trade-offs

**For Low Latency** (fast training, fast inference):
```python
config = EmbeddingConfig(
    model_name="sentence-transformers/paraphrase-MiniLM-L3-v2",
    batch_size=512,
    normalize=True,
)
```

**For High Quality** (better recommendations, slower):
```python
config = EmbeddingConfig(
    model_name="sentence-transformers/all-mpnet-base-v2",
    batch_size=128,
    normalize=True,
)
```

## ANN Configuration

Controls the approximate nearest neighbor search index.

```python
from pocket_recs.config import ANNConfig

ann_config = ANNConfig(
    backend="hnswlib",
    M=16,
    ef_construction=200,
    ef_search=64,
    metric="ip",
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | str | `hnswlib` | Backend: "hnswlib" or "faiss" |
| `M` | int | 16 | HNSW graph connectivity |
| `ef_construction` | int | 200 | Build-time search depth |
| `ef_search` | int | 64 | Query-time search depth |
| `metric` | str | `ip` | Distance metric: "ip" or "l2" |
| `index_type` | str | `HNSW` | FAISS index type (if backend=faiss) |
| `nlist` | int | 100 | Number of clusters (for IVF index) |

### Parameter Effects

**M (Graph Connectivity)**:
- Higher M = Better recall, more memory, slower build
- Lower M = Faster build, less memory, worse recall
- Recommended: 12-32

**ef_construction (Build Quality)**:
- Higher = Better index quality, slower build
- Lower = Faster build, worse quality
- Recommended: 100-400

**ef_search (Query Quality)**:
- Higher = Better recall, slower queries
- Lower = Faster queries, worse recall
- Recommended: 32-128

### Configurations by Use Case

**Fast Build (Development)**:
```python
ann_config = ANNConfig(
    backend="hnswlib",
    M=12,
    ef_construction=100,
    ef_search=32,
)
```

**Balanced (Default)**:
```python
ann_config = ANNConfig(
    backend="hnswlib",
    M=16,
    ef_construction=200,
    ef_search=64,
)
```

**High Quality (Production)**:
```python
ann_config = ANNConfig(
    backend="hnswlib",
    M=32,
    ef_construction=400,
    ef_search=128,
)
```

**Large Catalog (>100K items)**:
```python
ann_config = ANNConfig(
    backend="faiss",
    index_type="IVF",
    nlist=1000,
    M=24,
    ef_construction=200,
    ef_search=64,
)
```

## Co-visitation Configuration

Controls item-to-item patterns from user sessions.

```python
from pocket_recs.config import CovisConfig

covis_config = CovisConfig(
    top_k=50,
    tau_ms=900000,  # 15 minutes
    session_gap_minutes=30,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top_k` | int | 50 | Items to keep per seed item |
| `tau_ms` | int | 900000 | Time decay window (milliseconds) |
| `session_gap_minutes` | int | 30 | Session inactivity threshold |

### Time Decay (tau_ms)

Controls how strongly items viewed together are related:

| tau_ms | Minutes | Use Case |
|--------|---------|----------|
| 300000 | 5 | Fast browsing (news, social) |
| 900000 | 15 | **Default** (e-commerce) |
| 1800000 | 30 | Slow browsing (real estate) |

**Formula**: `score = exp(-time_diff / tau_ms)`

### Session Gap

Defines when a new session starts:

| Minutes | Use Case |
|---------|----------|
| 15 | Short sessions (quick purchases) |
| 30 | **Default** (typical e-commerce) |
| 60 | Long sessions (research purchases) |

### Optimization Examples

**High Engagement Site**:
```python
covis_config = CovisConfig(
    top_k=100,  # More related items
    tau_ms=300000,  # 5 minutes
    session_gap_minutes=15,
)
```

**Slow Browsing**:
```python
covis_config = CovisConfig(
    top_k=50,
    tau_ms=1800000,  # 30 minutes
    session_gap_minutes=60,
)
```

## Brand Popularity Configuration

Controls trending items per brand.

```python
from pocket_recs.config import BrandPopConfig

brand_pop_config = BrandPopConfig(
    half_life_days=7,
    top_n=100,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `half_life_days` | int | 7 | Popularity decay half-life |
| `top_n` | int | 100 | Items to keep per brand |

### Half-Life Effects

Controls how quickly popularity decays:

| Half-Life | Use Case |
|-----------|----------|
| 3 days | Fast-moving items (fashion, news) |
| 7 days | **Default** (general e-commerce) |
| 14 days | Stable catalog (books, tools) |
| 30 days | Long-tail products |

**Formula**: After `half_life_days`, an interaction has 50% of its original weight.

### Examples

**Fast Fashion**:
```python
brand_pop_config = BrandPopConfig(
    half_life_days=3,  # Recent trends matter
    top_n=50,  # Focus on top items
)
```

**Stable Catalog**:
```python
brand_pop_config = BrandPopConfig(
    half_life_days=30,  # Long-term popularity
    top_n=200,  # More diversity
)
```

## MMR Configuration

Controls result diversification.

```python
from pocket_recs.config import MMRConfig

mmr_config = MMRConfig(
    lambda_param=0.7,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lambda_param` | float | 0.7 | Relevance vs diversity (0-1) |

### Lambda Effects

| Value | Behavior | Use Case |
|-------|----------|----------|
| 0.0 | Maximum diversity | Exploration |
| 0.3 | High diversity | Discovery |
| 0.5 | Balanced | General use |
| 0.7 | **Default** (more relevant) | Precision |
| 1.0 | Pure relevance (no diversity) | Narrow search |

### Examples

**Exploration Mode**:
```python
mmr_config = MMRConfig(lambda_param=0.3)
```

**Precision Mode**:
```python
mmr_config = MMRConfig(lambda_param=0.9)
```

## Candidate Sizes

Controls how many candidates to retrieve from each source.

```python
candidate_sizes = {
    "covis": 40,
    "brand_pop": 40,
    "ann": 80,
    "item2vec": 40,
}
```

### Parameters

| Source | Default | Description |
|--------|---------|-------------|
| `covis` | 40 | Co-visitation candidates |
| `brand_pop` | 40 | Brand popularity candidates |
| `ann` | 80 | ANN semantic candidates |
| `item2vec` | 40 | Item2vec candidates (future) |

### Trade-offs

**More Candidates**:
- Pros: Better quality, more diversity
- Cons: Slower inference, more memory

**Fewer Candidates**:
- Pros: Faster inference, less memory
- Cons: May miss good items

### Examples

**Fast Inference**:
```python
candidate_sizes = {
    "covis": 20,
    "brand_pop": 20,
    "ann": 40,
}
```

**High Quality**:
```python
candidate_sizes = {
    "covis": 80,
    "brand_pop": 80,
    "ann": 160,
}
```

## Complete Configuration Examples

### Example 1: Development (Fast Training)

```python
from pocket_recs.config import RecommenderConfig, EmbeddingConfig, ANNConfig

config = RecommenderConfig(
    embedding=EmbeddingConfig(
        model_name="sentence-transformers/paraphrase-MiniLM-L3-v2",
        batch_size=512,
    ),
    ann=ANNConfig(
        M=12,
        ef_construction=100,
        ef_search=32,
    ),
    candidate_sizes={
        "covis": 20,
        "brand_pop": 20,
        "ann": 40,
    },
)
```

**Characteristics**:
- Training: ~5 minutes (10K items)
- Inference: ~10ms
- Quality: Good

### Example 2: Production (Balanced)

```python
config = RecommenderConfig(
    embedding=EmbeddingConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        batch_size=256,
    ),
    ann=ANNConfig(
        M=16,
        ef_construction=200,
        ef_search=64,
    ),
    covis=CovisConfig(
        top_k=50,
        tau_ms=900000,
        session_gap_minutes=30,
    ),
    brand_pop=BrandPopConfig(
        half_life_days=7,
        top_n=100,
    ),
    mmr=MMRConfig(
        lambda_param=0.7,
    ),
    candidate_sizes={
        "covis": 40,
        "brand_pop": 40,
        "ann": 80,
    },
)
```

**Characteristics**:
- Training: ~10 minutes (10K items)
- Inference: ~20ms
- Quality: Very good (default configuration)

### Example 3: High Quality

```python
config = RecommenderConfig(
    embedding=EmbeddingConfig(
        model_name="sentence-transformers/all-mpnet-base-v2",
        batch_size=128,
    ),
    ann=ANNConfig(
        M=32,
        ef_construction=400,
        ef_search=128,
    ),
    covis=CovisConfig(
        top_k=100,
    ),
    brand_pop=BrandPopConfig(
        top_n=200,
    ),
    mmr=MMRConfig(
        lambda_param=0.5,  # More diversity
    ),
    candidate_sizes={
        "covis": 80,
        "brand_pop": 80,
        "ann": 160,
    },
)
```

**Characteristics**:
- Training: ~30 minutes (10K items)
- Inference: ~40ms
- Quality: Excellent

### Example 4: Large Catalog (100K+ items)

```python
config = RecommenderConfig(
    embedding=EmbeddingConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        batch_size=256,
    ),
    ann=ANNConfig(
        backend="faiss",
        index_type="IVF",
        nlist=1000,
        M=24,
        ef_construction=200,
        ef_search=64,
    ),
    covis=CovisConfig(
        top_k=50,
    ),
    brand_pop=BrandPopConfig(
        top_n=100,
    ),
    candidate_sizes={
        "covis": 40,
        "brand_pop": 40,
        "ann": 80,
    },
)
```

**Characteristics**:
- Scales to 100K+ items
- Training: ~1 hour (100K items)
- Inference: ~30ms
- Quality: Good

## Performance Tuning Guide

### Goal: Minimize Training Time

1. **Use faster embedding model**:
   ```python
   model_name="sentence-transformers/paraphrase-MiniLM-L3-v2"
   ```

2. **Increase batch size** (if RAM allows):
   ```python
   batch_size=512
   ```

3. **Reduce ANN index quality**:
   ```python
   M=12
   ef_construction=100
   ```

### Goal: Minimize Inference Latency

1. **Reduce ef_search**:
   ```python
   ef_search=32
   ```

2. **Reduce candidate sizes**:
   ```python
   candidate_sizes={"covis": 20, "brand_pop": 20, "ann": 40}
   ```

3. **Lower MMR lambda** (faster diversity calc):
   ```python
   lambda_param=0.9
   ```

### Goal: Maximize Quality

1. **Use better embedding model**:
   ```python
   model_name="sentence-transformers/all-mpnet-base-v2"
   ```

2. **Increase ANN search quality**:
   ```python
   ef_search=128
   M=32
   ```

3. **Increase candidate pool**:
   ```python
   candidate_sizes={"covis": 80, "brand_pop": 80, "ann": 160}
   ```

### Goal: Maximize Diversity

1. **Lower MMR lambda**:
   ```python
   lambda_param=0.3
   ```

2. **Increase candidate pool sizes**:
   ```python
   candidate_sizes={"covis": 80, "brand_pop": 80, "ann": 160}
   ```

3. **Increase brand_pop.top_n**:
   ```python
   top_n=200
   ```

## Loading Custom Configuration

### From Python

```python
from pocket_recs import fit, Recommender
from pocket_recs.config import RecommenderConfig

# Create config
config = RecommenderConfig(...)

# Use in training
artifacts_dir = fit(
    interactions_path="interactions.parquet",
    catalog_path="catalog.csv",
    out_dir="artifacts/",
    config=config
)

# Use in inference
recommender = Recommender(
    artifacts_dir="artifacts/",
    catalog_path="catalog.csv",
    config=config
)
```

### From YAML (Advanced)

```yaml
# config.yaml
embedding:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  batch_size: 256
  normalize: true

ann:
  M: 16
  ef_construction: 200
  ef_search: 64

covis:
  top_k: 50
  tau_ms: 900000
  session_gap_minutes: 30

brand_pop:
  half_life_days: 7
  top_n: 100

mmr:
  lambda_param: 0.7

candidate_sizes:
  covis: 40
  brand_pop: 40
  ann: 80
```

```python
import yaml
from pocket_recs.config import RecommenderConfig

# Load from YAML
with open("config.yaml") as f:
    config_dict = yaml.safe_load(f)

config = RecommenderConfig(**config_dict)
```

## Next Steps

- **[Advanced Features](08-advanced-features.md)**: Explore advanced capabilities
- **[Production Deployment](09-production-deployment.md)**: Deploy to production
- **[Troubleshooting](11-troubleshooting.md)**: Resolve configuration issues

---

Fine-tune Pocket-Recs for your specific use case!

