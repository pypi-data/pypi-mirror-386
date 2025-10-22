# Online Recommendations

This guide covers how to use trained models to generate recommendations at inference time.

## Overview

Once you've trained your model, you can load the recommender and start generating personalized recommendations. The inference process is fast (10-50ms) and runs entirely on CPU.

## Quick Start

### Load the Recommender

```python
from pocket_recs import Recommender

recommender = Recommender(
    artifacts_dir="artifacts/",
    catalog_path="catalog.csv"
)
```

### Generate Recommendations

```python
from pocket_recs.types import RecommendRequest, Interaction

request = RecommendRequest(
    user_id="user_123",
    k=10,
    recent=[
        Interaction(
            user_id="user_123",
            item_id="item_5",
            timestamp=1700000000000,
            event="view"
        )
    ]
)

response = recommender.recommend(request)

for item in response.items:
    print(f"{item.rank}. {item.item_id} - Score: {item.score:.3f}")
    print(f"   Reasons: {', '.join(item.reasons)}")
```

## RecommendRequest Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | str | User identifier (can be session ID for anonymous users) |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `k` | int | 20 | Number of recommendations to return (1-100) |
| `recent` | List[Interaction] | [] | Recent user interactions |
| `brand` | str | None | Filter to specific brand |
| `exclusions` | List[str] | [] | Item IDs to exclude from results |
| `filters` | dict | {} | Additional custom filters |

### Interaction Object

Each interaction in the `recent` list should have:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | str | Yes | User identifier |
| `item_id` | str | Yes | Item identifier |
| `timestamp` | int | Yes | Unix timestamp in milliseconds |
| `event` | str | Yes | Event type: "view", "add", or "purchase" |
| `brand` | str | No | Brand name |
| `quantity` | int | No | Quantity (default: 1) |
| `price` | float | No | Price |

## Response Format

The `recommend()` method returns a `RecommendResponse` object:

```python
response = recommender.recommend(request)

# Access recommendations
for item in response.items:
    print(f"Item ID: {item.item_id}")
    print(f"Score: {item.score}")
    print(f"Rank: {item.rank}")
    print(f"Reasons: {item.reasons}")
```

### RecommendResponse Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | List[RecommendItem] | List of recommended items |
| `artifact_version` | str | Version of artifacts used |
| `metadata` | dict | Additional metadata (candidates count, etc.) |

### RecommendItem Fields

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | str | Unique item identifier |
| `score` | float | Combined score (higher = better) |
| `rank` | int | Position in ranking (1 = best) |
| `reasons` | List[str] | Why this item was recommended |

## Common Use Cases

### Use Case 1: Personalized Homepage

Show recommendations based on user's browsing history.

```python
from pocket_recs import Recommender
from pocket_recs.types import RecommendRequest, Interaction
import time

recommender = Recommender(
    artifacts_dir="artifacts/",
    catalog_path="catalog.csv"
)

def get_homepage_recommendations(user_id: str, recent_views: List[str]) -> List[str]:
    """Get personalized homepage recommendations."""
    
    # Convert recent views to Interaction objects
    current_time = int(time.time() * 1000)
    recent = [
        Interaction(
            user_id=user_id,
            item_id=item_id,
            timestamp=current_time - (i * 60000),  # 1 minute apart
            event="view"
        )
        for i, item_id in enumerate(reversed(recent_views[:5]))  # Last 5 views
    ]
    
    request = RecommendRequest(
        user_id=user_id,
        k=12,  # Show 12 items on homepage
        recent=recent
    )
    
    response = recommender.recommend(request)
    return [item.item_id for item in response.items]

# Usage
user_recent_views = ["item_10", "item_25", "item_42"]
recommendations = get_homepage_recommendations("user_123", user_recent_views)
print(f"Recommended: {recommendations}")
```

### Use Case 2: Product Detail Page

Show "you may also like" on product pages.

```python
def get_similar_items(item_id: str, exclude_item_id: str = None, k: int = 6) -> List[str]:
    """Get similar items for product detail page."""
    
    current_time = int(time.time() * 1000)
    
    # Create a pseudo-user based on this item view
    request = RecommendRequest(
        user_id=f"temp_{item_id}",  # Temporary user ID
        k=k,
        recent=[
            Interaction(
                user_id=f"temp_{item_id}",
                item_id=item_id,
                timestamp=current_time,
                event="view"
            )
        ],
        exclusions=[exclude_item_id or item_id]  # Don't recommend the same item
    )
    
    response = recommender.recommend(request)
    return [item.item_id for item in response.items]

# Usage
similar_items = get_similar_items("item_42", k=6)
print(f"You may also like: {similar_items}")
```

### Use Case 3: Shopping Cart Recommendations

Show items to add based on cart contents.

```python
def get_cart_recommendations(user_id: str, cart_items: List[str]) -> List[str]:
    """Get recommendations based on shopping cart."""
    
    current_time = int(time.time() * 1000)
    
    # Treat cart items as recent "add" events
    recent = [
        Interaction(
            user_id=user_id,
            item_id=item_id,
            timestamp=current_time - (i * 60000),
            event="add"  # These were added to cart
        )
        for i, item_id in enumerate(cart_items)
    ]
    
    request = RecommendRequest(
        user_id=user_id,
        k=8,
        recent=recent,
        exclusions=cart_items  # Don't recommend items already in cart
    )
    
    response = recommender.recommend(request)
    return [item.item_id for item in response.items]

# Usage
cart = ["item_10", "item_25"]
add_to_cart_recs = get_cart_recommendations("user_123", cart)
print(f"Customers also bought: {add_to_cart_recs}")
```

### Use Case 4: Brand-Specific Recommendations

Show items from a specific brand.

```python
def get_brand_recommendations(user_id: str, brand: str, k: int = 10) -> List[str]:
    """Get recommendations for a specific brand."""
    
    request = RecommendRequest(
        user_id=user_id,
        k=k,
        recent=[],  # Can include recent interactions if available
        brand=brand  # Focus on this brand
    )
    
    response = recommender.recommend(request)
    return [item.item_id for item in response.items]

# Usage
nike_recs = get_brand_recommendations("user_123", "Nike", k=10)
print(f"Nike recommendations: {nike_recs}")
```

### Use Case 5: Cold Start (New User)

Handle users with no history.

```python
def get_cold_start_recommendations(k: int = 10) -> List[str]:
    """Get recommendations for new users with no history."""
    
    request = RecommendRequest(
        user_id="new_user",  # Or use session ID
        k=k,
        recent=[]  # Empty history
    )
    
    response = recommender.recommend(request)
    return [item.item_id for item in response.items]

# Usage
trending = get_cold_start_recommendations(k=10)
print(f"Trending items: {trending}")
```

### Use Case 6: Post-Purchase Recommendations

Show complementary items after purchase.

```python
def get_post_purchase_recommendations(
    user_id: str, 
    purchased_items: List[str],
    k: int = 8
) -> List[str]:
    """Get recommendations after purchase (cross-sell)."""
    
    current_time = int(time.time() * 1000)
    
    # Mark as purchases
    recent = [
        Interaction(
            user_id=user_id,
            item_id=item_id,
            timestamp=current_time,
            event="purchase"  # These were purchased
        )
        for item_id in purchased_items
    ]
    
    request = RecommendRequest(
        user_id=user_id,
        k=k,
        recent=recent,
        exclusions=purchased_items  # Don't recommend same items
    )
    
    response = recommender.recommend(request)
    return [item.item_id for item in response.items]

# Usage
purchased = ["item_42"]
cross_sell = get_post_purchase_recommendations("user_123", purchased)
print(f"Complete your order with: {cross_sell}")
```

### Use Case 7: Email Campaigns

Generate personalized recommendations for email campaigns.

```python
import polars as pl
from typing import Dict, List

def generate_email_recommendations(
    user_ids: List[str],
    interactions_df: pl.DataFrame,
    k: int = 5
) -> Dict[str, List[str]]:
    """Generate recommendations for email campaign."""
    
    results = {}
    current_time = int(time.time() * 1000)
    
    for user_id in user_ids:
        # Get user's recent activity (last 30 days)
        cutoff = current_time - (30 * 24 * 3600 * 1000)
        user_history = interactions_df.filter(
            (pl.col("user_id") == user_id) &
            (pl.col("timestamp") >= cutoff)
        ).sort("timestamp", descending=True).head(10)
        
        # Convert to Interaction objects
        recent = [
            Interaction(
                user_id=row["user_id"],
                item_id=row["item_id"],
                timestamp=row["timestamp"],
                event=row["event"]
            )
            for row in user_history.iter_rows(named=True)
        ]
        
        # Get recommendations
        request = RecommendRequest(
            user_id=user_id,
            k=k,
            recent=recent
        )
        
        response = recommender.recommend(request)
        results[user_id] = [item.item_id for item in response.items]
    
    return results

# Usage
interactions = pl.read_parquet("interactions.parquet")
email_list = ["user_001", "user_002", "user_003"]
recommendations_by_user = generate_email_recommendations(email_list, interactions)

for user_id, recs in recommendations_by_user.items():
    print(f"{user_id}: {recs}")
```

## Advanced Features

### Filtering Seen Items

Automatically exclude items the user has already interacted with:

```python
import polars as pl

def get_recommendations_excluding_history(
    user_id: str,
    interactions_df: pl.DataFrame,
    k: int = 10
) -> List[str]:
    """Get recommendations, excluding all previously seen items."""
    
    # Get all items user has seen
    user_history = interactions_df.filter(pl.col("user_id") == user_id)
    seen_items = user_history["item_id"].unique().to_list()
    
    # Get recent interactions (last 5)
    recent_interactions = user_history.sort("timestamp", descending=True).head(5)
    recent = [
        Interaction(
            user_id=row["user_id"],
            item_id=row["item_id"],
            timestamp=row["timestamp"],
            event=row["event"]
        )
        for row in recent_interactions.iter_rows(named=True)
    ]
    
    # Request recommendations, excluding seen items
    request = RecommendRequest(
        user_id=user_id,
        k=k,
        recent=recent,
        exclusions=seen_items  # Exclude everything they've seen
    )
    
    response = recommender.recommend(request)
    return [item.item_id for item in response.items]
```

### Hybrid User-Item Recommendations

Combine user preferences with specific item context:

```python
def get_hybrid_recommendations(
    user_id: str,
    current_item_id: str,
    recent_views: List[str],
    k: int = 10
) -> List[str]:
    """Hybrid: user preferences + current item context."""
    
    current_time = int(time.time() * 1000)
    
    # Combine recent views with current item
    all_items = [current_item_id] + recent_views[:4]  # Weight current item
    
    recent = [
        Interaction(
            user_id=user_id,
            item_id=item_id,
            timestamp=current_time - (i * 60000),
            event="view"
        )
        for i, item_id in enumerate(all_items)
    ]
    
    request = RecommendRequest(
        user_id=user_id,
        k=k,
        recent=recent,
        exclusions=[current_item_id] + recent_views
    )
    
    response = recommender.recommend(request)
    return [item.item_id for item in response.items]
```

### Diversity Control

Adjust diversity through the MMR lambda parameter (requires custom config):

```python
from pocket_recs.config import RecommenderConfig, MMRConfig

# More diverse recommendations
config = RecommenderConfig(
    mmr=MMRConfig(lambda_param=0.3)  # Lower = more diverse
)

recommender = Recommender(
    artifacts_dir="artifacts/",
    catalog_path="catalog.csv",
    config=config
)

# Or more relevant (less diverse)
config = RecommenderConfig(
    mmr=MMRConfig(lambda_param=0.9)  # Higher = more relevant
)
```

## Performance Optimization

### Caching Recommendations

For frequently accessed users/items:

```python
from functools import lru_cache
from typing import Tuple

@lru_cache(maxsize=10000)
def get_cached_recommendations(
    user_id: str,
    recent_items: Tuple[str, ...],  # Must be hashable (tuple, not list)
    k: int
) -> List[str]:
    """Cache recommendations for frequently requested combinations."""
    
    current_time = int(time.time() * 1000)
    
    recent = [
        Interaction(
            user_id=user_id,
            item_id=item_id,
            timestamp=current_time - (i * 60000),
            event="view"
        )
        for i, item_id in enumerate(recent_items)
    ]
    
    request = RecommendRequest(user_id=user_id, k=k, recent=recent)
    response = recommender.recommend(request)
    
    return [item.item_id for item in response.items]

# Usage (convert list to tuple for caching)
recs = get_cached_recommendations(
    "user_123",
    tuple(["item_5", "item_10"]),  # Tuple, not list
    k=10
)
```

### Batch Processing

Process multiple users efficiently:

```python
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

def batch_recommend(
    user_requests: List[Dict],
    max_workers: int = 4
) -> List[List[str]]:
    """Process multiple recommendation requests in parallel."""
    
    def process_request(req_data: Dict) -> List[str]:
        request = RecommendRequest(
            user_id=req_data["user_id"],
            k=req_data.get("k", 10),
            recent=req_data.get("recent", [])
        )
        response = recommender.recommend(request)
        return [item.item_id for item in response.items]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_request, user_requests))
    
    return results

# Usage
requests = [
    {"user_id": "user_001", "k": 10, "recent": []},
    {"user_id": "user_002", "k": 10, "recent": []},
    {"user_id": "user_003", "k": 10, "recent": []},
]

results = batch_recommend(requests, max_workers=4)
print(f"Processed {len(results)} users")
```

## Performance Benchmarks

| Catalog Size | Cold Start | With History | Memory |
|--------------|------------|--------------|--------|
| 10K items | 8-15ms | 10-20ms | 1 GB |
| 50K items | 15-25ms | 20-30ms | 2 GB |
| 100K items | 20-40ms | 30-50ms | 4 GB |

Benchmarks on 2 vCPU / 4-8 GB RAM

## Troubleshooting

### Slow Inference

**Problem**: Recommendations taking >100ms

**Solutions**:
1. Reduce `ef_search` in ANN config
2. Enable caching for frequent requests
3. Use smaller embedding model
4. Reduce candidate pool sizes

### Low Diversity

**Problem**: All recommendations very similar

**Solutions**:
1. Lower `lambda_param` in MMR config (e.g., 0.3)
2. Increase candidate pool size
3. Check if catalog has sufficient variety

### Poor Cold Start

**Problem**: Bad recommendations for new users

**Solutions**:
1. Ensure brand popularity is computed correctly
2. Check that catalog has good metadata
3. Consider showing trending/popular items

## Next Steps

- **[API Guide](06-api-guide.md)**: Deploy as REST API
- **[Configuration](07-configuration.md)**: Tune performance and quality
- **[Advanced Features](08-advanced-features.md)**: Explore more capabilities
- **[Production Deployment](09-production-deployment.md)**: Go to production

---

Fast, flexible recommendations tailored to your use case!

