# Core Concepts

This guide explains how Pocket-Recs works under the hood, helping you understand the architecture and make informed decisions about configuration.

## Architecture Overview

Pocket-Recs uses a **multi-stage hybrid pipeline** to generate recommendations:

```
┌─────────────────────────────────────────────────────────────────┐
│                        OFFLINE TRAINING                          │
├─────────────────────────────────────────────────────────────────┤
│  Interactions + Catalog                                          │
│         │                                                         │
│         ├──> Sessionize                                          │
│         ├──> Co-visitation Matrix                                │
│         ├──> Brand Popularity                                    │
│         ├──> Text Embeddings                                     │
│         └──> ANN Index (HNSW/FAISS)                              │
│                                                                   │
│  Output: Artifacts Directory                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      ONLINE INFERENCE                            │
├─────────────────────────────────────────────────────────────────┤
│  User Request (user_id + recent interactions)                   │
│         │                                                         │
│         ├──> Build User Vector                                   │
│         │                                                         │
│         ├──> [Retrieval Stage]                                   │
│         │    ├─> Co-visitation Candidates                        │
│         │    ├─> Brand Popularity Candidates                     │
│         │    └─> ANN Semantic Candidates                         │
│         │                                                         │
│         ├──> [Candidate Pool: ~100-200 items]                    │
│         │                                                         │
│         ├──> [Ranking Stage]                                     │
│         │    └─> Combine signals and score                       │
│         │                                                         │
│         ├──> [Diversification Stage]                             │
│         │    └─> MMR (Maximal Marginal Relevance)                │
│         │                                                         │
│         └──> Top-K Results + Reasons                             │
└─────────────────────────────────────────────────────────────────┘
```

## Offline Training Pipeline

The offline training phase prepares all the components needed for fast online inference.

### 1. Sessionization

**Purpose**: Group user interactions into sessions for co-visitation analysis.

**How it works**:
- Groups interactions by user
- Splits into sessions based on time gaps (default: 30 minutes)
- Session = continuous period of user activity

**Why it matters**: Co-visitation patterns work better when computed within sessions rather than across all user history.

### 2. Co-visitation Matrix

**Purpose**: Capture "users who viewed X also viewed Y" patterns.

**How it works**:
- For each session, finds items viewed together
- Applies time decay: items viewed closer together have higher weight
- Stores top-K co-visited items per seed item
- Uses sparse matrix format for efficiency

**Parameters**:
- `top_k`: Number of related items per seed (default: 50)
- `tau_ms`: Time decay window in milliseconds (default: 15 minutes)

**Example**:
```
User session: [item_1, item_2, item_3]
Co-visitation matrix:
  item_1 -> [item_2: 0.9, item_3: 0.7]
  item_2 -> [item_1: 0.9, item_3: 0.8]
  item_3 -> [item_1: 0.7, item_2: 0.8]
```

### 3. Brand Popularity

**Purpose**: Track popular items within each brand with recency weighting.

**How it works**:
- Counts interactions (views, adds, purchases) per brand-item
- Applies exponential decay based on interaction age
- Keeps top-N items per brand

**Parameters**:
- `half_life_days`: How quickly popularity decays (default: 7 days)
- `top_n`: Keep top N items per brand (default: 100)

**Why it matters**: Helps with cold start and brand-focused recommendations.

### 4. Text Embeddings

**Purpose**: Convert item metadata into vector representations for semantic similarity.

**How it works**:
- Combines: title + brand + category + short_desc
- Uses sentence-transformers models (e.g., all-MiniLM-L6-v2)
- Generates 384-dimensional vectors (model-dependent)
- L2-normalizes for cosine similarity

**Example**:
```
Item: "Nike Air Zoom Pegasus 40 Running Shoe"
Text: "Nike Air Zoom Pegasus 40 Running Shoe Nike Footwear Premium..."
Embedding: [0.023, -0.145, 0.087, ..., 0.234] (384 dims)
```

**Why it matters**: Enables semantic search - finds items similar in meaning, not just keywords.

### 5. ANN Index

**Purpose**: Fast approximate nearest neighbor search in embedding space.

**How it works**:
- Builds HNSW (Hierarchical Navigable Small World) graph
- Each item = node, edges connect similar items
- Query traverses graph to find nearest neighbors in milliseconds

**Parameters**:
- `M`: Graph connectivity (higher = better recall, more memory)
- `ef_construction`: Build-time search depth (higher = better quality)
- `ef_search`: Query-time search depth (higher = slower, more accurate)

**Performance**: O(log N) search time instead of O(N) brute force.

## Online Inference Pipeline

### Stage 1: Candidate Retrieval

**Goal**: Quickly fetch 100-200 candidate items from multiple sources.

#### A. Co-visitation Candidates

**How**:
1. Take user's last 5 interactions
2. Look up co-visited items for each
3. Aggregate and deduplicate
4. Boost score by +0.3

**Example**:
```python
User viewed: [item_5, item_10]
Co-visitation lookup:
  item_5 -> [item_15: 0.8, item_20: 0.6]
  item_10 -> [item_15: 0.7, item_25: 0.5]
Candidates: [item_15 (boost: 0.3), item_20 (boost: 0.3), item_25 (boost: 0.3)]
```

#### B. Brand Popularity Candidates

**How**:
1. Identify user's preferred brands (from recent interactions or history)
2. Fetch top-N popular items from those brands
3. Boost score by +0.15

**Example**:
```python
User prefers: Brand_0
Brand popularity lookup:
  Brand_0 -> [item_7: 0.9, item_12: 0.8, item_23: 0.7]
Candidates: [item_7 (boost: 0.15), item_12 (boost: 0.15), item_23 (boost: 0.15)]
```

#### C. ANN Semantic Candidates

**How**:
1. Build user vector: average embeddings of recent interactions
2. Query ANN index for top-80 similar items
3. Use similarity score as-is

**Example**:
```python
User vector: avg([embedding(item_5), embedding(item_10)])
ANN search:
  Top results: [item_42: 0.87, item_38: 0.82, item_51: 0.79, ...]
Candidates: [item_42 (score: 0.87), item_38 (score: 0.82), ...]
```

**Candidate Pool Size**:
- Co-visitation: ~40 items
- Brand Popularity: ~40 items
- ANN: ~80 items
- **Total: ~100-200 candidates** (with overlap)

### Stage 2: Scoring and Ranking

**Goal**: Combine signals from all sources into a final score.

**Scoring Formula**:
```
Final Score = ANN Similarity + Co-visitation Boost + Brand Boost

Where:
  ANN Similarity: 0.0 - 1.0 (cosine similarity)
  Co-visitation Boost: +0.3 if from co-visitation
  Brand Boost: +0.15 if from brand popularity
```

**Example**:
```
Item A: 
  - ANN similarity: 0.75
  - Co-visited: Yes (+0.3)
  - Brand popular: Yes (+0.15)
  - Final score: 0.75 + 0.3 + 0.15 = 1.20

Item B:
  - ANN similarity: 0.85
  - Co-visited: No
  - Brand popular: No
  - Final score: 0.85
```

**Optional**: LightGBM ranker can be trained to learn optimal scoring (advanced).

### Stage 3: Diversification (MMR)

**Goal**: Balance relevance with diversity to avoid repetitive recommendations.

**How MMR works**:
1. Start with empty result set
2. Iteratively select items:
   - High relevance score
   - Low similarity to already-selected items
3. Lambda parameter controls trade-off:
   - Lambda = 1.0: Pure relevance (no diversity)
   - Lambda = 0.0: Maximum diversity (ignore relevance)
   - Lambda = 0.5: Balanced (default)

**Formula**:
```
MMR Score = lambda * Relevance - (1 - lambda) * max(Similarity to Selected)
```

**Example**:
```
Candidates: [item_A: 0.9, item_B: 0.85, item_C: 0.80]
Assume item_A and item_B are very similar (0.95)

With lambda=0.5:
1. Select item_A (score: 0.9)
2. Item_B: 0.5*0.85 - 0.5*0.95 = 0.425 - 0.475 = -0.05 (penalized!)
3. Item_C: 0.5*0.80 - 0.5*0.60 = 0.400 - 0.300 = 0.10 (preferred)
Result: [item_A, item_C, item_B]
```

**Why it matters**: Prevents showing 10 nearly-identical items.

### Stage 4: Explanation

**Goal**: Provide transparent reason codes for each recommendation.

**Reason Codes**:

| Code | Condition |
|------|-----------|
| `co-visited` | Item came from co-visitation matrix |
| `brand-popular` | Item came from brand popularity |
| `semantic` | Item came from ANN search (high similarity) |
| `baseline` | Fallback (general popularity) |

**Example**:
```json
{
  "item_id": "item_42",
  "score": 1.15,
  "reasons": ["semantic", "brand-popular"],
  "rank": 1
}
```

## Key Design Decisions

### Why Hybrid?

Single-strategy systems have limitations:

| Strategy | Strength | Weakness |
|----------|----------|----------|
| Collaborative Filtering | Captures user patterns | Cold start problem |
| Content-Based | Works for new items | Limited to metadata |
| Popularity | Always works | Not personalized |

**Hybrid approach** combines strengths, mitigates weaknesses.

### Why CPU-Only?

**Advantages**:
- Lower infrastructure costs ($5-25/month vs $500+/month)
- Easier deployment (no GPU drivers, CUDA, etc.)
- Better for edge/serverless scenarios
- Sufficient for catalogs up to 100K items

**Trade-offs**:
- Slightly slower training (minutes vs seconds)
- Limited to smaller embedding models
- Not ideal for >1M items

### Why Multi-Stage Pipeline?

**Stage 1 (Retrieval)**: Fast, approximate
- Goal: Reduce 100K items to ~200 candidates
- Latency: ~5-10ms

**Stage 2 (Ranking)**: Slower, accurate
- Goal: Precisely score 200 candidates
- Latency: ~5-10ms

**Stage 3 (Diversification)**: Quality improvement
- Goal: Improve user experience
- Latency: ~2-5ms

**Total latency**: ~15-30ms (acceptable for most use cases)

## Data Flow Example

Let's trace a complete recommendation request:

**Input**:
```python
request = RecommendRequest(
    user_id="user_123",
    k=5,
    recent=[
        Interaction(user_id="user_123", item_id="item_5", event="view"),
        Interaction(user_id="user_123", item_id="item_10", event="add")
    ]
)
```

**Step 1: Build User Vector**
```
user_vector = avg(embedding(item_5), embedding(item_10))
```

**Step 2: Retrieve Candidates**
```
Co-visitation:
  item_5 -> [item_15, item_20]
  item_10 -> [item_15, item_25]
  Candidates: [item_15, item_20, item_25]

Brand Popularity:
  User brands: [Brand_0, Brand_1]
  Brand_0 -> [item_7, item_12]
  Brand_1 -> [item_8]
  Candidates: [item_7, item_12, item_8]

ANN Search:
  query(user_vector, k=80)
  Candidates: [item_42, item_38, item_51, ...]

Total: ~100 candidates
```

**Step 3: Score**
```
item_15: 0.82 (ANN) + 0.3 (covis) + 0.15 (brand) = 1.27
item_42: 0.87 (ANN) = 0.87
item_7:  0.75 (ANN) + 0.15 (brand) = 0.90
...
```

**Step 4: MMR**
```
Sorted: [item_15: 1.27, item_7: 0.90, item_42: 0.87, ...]
Apply diversity:
  -> [item_15, item_42, item_7, ...]
```

**Step 5: Add Reasons**
```json
[
  {"item_id": "item_15", "score": 1.27, "reasons": ["co-visited", "brand-popular", "semantic"]},
  {"item_id": "item_42", "score": 0.87, "reasons": ["semantic"]},
  {"item_id": "item_7", "score": 0.90, "reasons": ["brand-popular", "semantic"]}
]
```

**Output**: Top-5 recommendations with explanations

## Performance Characteristics

| Catalog Size | Training Time | Inference Latency | Memory |
|--------------|---------------|-------------------|--------|
| 10K items | 5-10 min | 10-20ms | 2 GB |
| 50K items | 15-30 min | 20-30ms | 4 GB |
| 100K items | 30-60 min | 30-50ms | 6 GB |

## Next Steps

- **[Data Preparation](03-data-preparation.md)**: Learn about data formats
- **[Offline Training](04-offline-training.md)**: Deep dive into training
- **[Configuration](07-configuration.md)**: Tune for your use case
- **[Advanced Features](08-advanced-features.md)**: Explore advanced capabilities

---

Understanding these core concepts will help you make informed decisions about configuration, troubleshooting, and optimization!

