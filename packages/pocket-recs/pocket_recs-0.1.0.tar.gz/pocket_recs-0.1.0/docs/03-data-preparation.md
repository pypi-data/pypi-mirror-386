# Data Preparation

This guide explains how to prepare your data for Pocket-Recs, including required formats, data quality best practices, and common transformations.

## Overview

Pocket-Recs requires two files:

1. **Catalog** (CSV): Your product/item catalog
2. **Interactions** (Parquet): User behavior data

## Catalog Data (CSV)

### Required Format

The catalog should be a CSV file with the following structure:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `item_id` | string | **Yes** | Unique identifier for each item |
| `title` | string | **Yes** | Item title or name |
| `brand` | string | No | Brand name |
| `category` | string | No | Product category |
| `short_desc` | string | No | Short description |
| `price` | float | No | Price in your currency |
| `in_stock` | boolean | No | Stock availability |

### Example Catalog

```csv
item_id,title,brand,category,short_desc,price,in_stock
item_001,Nike Air Zoom Pegasus 40,Nike,Running Shoes,Premium running shoe with responsive cushioning,129.99,true
item_002,Adidas Ultraboost 22,Adidas,Running Shoes,Energy-returning running shoe,190.00,true
item_003,Apple AirPods Pro,Apple,Electronics,Active noise cancellation wireless earbuds,249.00,true
item_004,Samsung Galaxy Buds,Samsung,Electronics,Wireless earbuds with long battery life,149.99,false
```

### Best Practices

#### 1. Item IDs
- Use **unique, stable identifiers** (don't change over time)
- Avoid special characters that need URL encoding
- Keep them reasonably short (< 50 characters)

**Good**: `product_12345`, `sku-abc-123`, `nike-air-zoom-40`  
**Bad**: `Product #12,345 (2023)`, `item with spaces!`, `really-long-identifier-that-goes-on-and-on-forever`

#### 2. Titles
- **Be descriptive**: Include key product attributes
- **Consistent formatting**: Use same style across all items
- **Include brand** if not in separate field

**Good**: `Nike Air Zoom Pegasus 40 Running Shoe`  
**Poor**: `Shoe`, `Product 123`

#### 3. Brands and Categories
- **Normalize**: Use consistent names (`Nike` not `nike`, `NIKE`, or `Nike, Inc.`)
- **Be specific but not too granular**: `Running Shoes` > `Athletic Footwear > Running > Road Running > Neutral`
- **Use brand/category even for cold items**: Helps with recommendations

#### 4. Descriptions
- **Keep them concise**: 50-200 characters ideal
- **Include key features**: Material, use case, unique selling points
- **Avoid marketing fluff**: Focus on factual attributes

**Good**: `Lightweight running shoe with carbon fiber plate and ZoomX foam for responsive cushioning`  
**Poor**: `Amazing! Best shoe ever! You'll love it! Buy now!`

#### 5. Price and Stock
- **Consistent currency**: Don't mix USD and EUR
- **Real numbers**: Use actual prices, not "Call for price"
- **Update stock regularly**: Helps filter recommendations

### Creating Catalog from Your Database

#### From SQL Database

```python
import polars as pl
import psycopg2  # or your DB driver

# Connect to database
conn = psycopg2.connect("postgresql://user:pass@localhost/db")

# Query products
query = """
    SELECT 
        product_id as item_id,
        product_name as title,
        brand_name as brand,
        category_name as category,
        description as short_desc,
        price,
        in_stock
    FROM products
    WHERE is_active = true
"""

# Load into Polars
catalog = pl.read_database(query, conn)

# Save as CSV
catalog.write_csv("catalog.csv")
```

#### From JSON/API

```python
import polars as pl
import requests

# Fetch from API
response = requests.get("https://api.example.com/products")
products = response.json()

# Transform to catalog format
catalog = pl.DataFrame({
    "item_id": [p["id"] for p in products],
    "title": [p["name"] for p in products],
    "brand": [p.get("brand", "") for p in products],
    "category": [p.get("category", "") for p in products],
    "short_desc": [p.get("description", "")[:200] for p in products],
    "price": [p.get("price", 0.0) for p in products],
    "in_stock": [p.get("stock", 0) > 0 for p in products],
})

catalog.write_csv("catalog.csv")
```

## Interaction Data (Parquet)

### Required Format

Interactions should be in Parquet format with:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `user_id` | string | **Yes** | User identifier |
| `item_id` | string | **Yes** | Item identifier (must match catalog) |
| `timestamp` | int64 | **Yes** | Unix timestamp in **milliseconds** |
| `event` | string | **Yes** | Event type: `view`, `add`, or `purchase` |
| `brand` | string | No | Brand at interaction time |
| `quantity` | int | No | Quantity (default: 1) |
| `price` | float | No | Price at interaction time |

### Example Interactions

```python
import polars as pl

interactions = pl.DataFrame({
    "user_id": ["user_001", "user_001", "user_002"],
    "item_id": ["item_001", "item_002", "item_001"],
    "timestamp": [1700000000000, 1700000100000, 1700000200000],
    "event": ["view", "add", "purchase"],
    "brand": ["Nike", "Adidas", "Nike"],
    "quantity": [1, 1, 2],
    "price": [129.99, 190.00, 129.99]
})

interactions.write_parquet("interactions.parquet")
```

### Best Practices

#### 1. Timestamps
**CRITICAL**: Use **milliseconds**, not seconds!

```python
# Correct (milliseconds)
timestamp = 1700000000000  # 13 digits

# Wrong (seconds)
timestamp = 1700000000  # 10 digits
```

**Converting from seconds**:
```python
timestamp_ms = timestamp_seconds * 1000
```

**From Python datetime**:
```python
import time
from datetime import datetime

# Current time
timestamp_ms = int(time.time() * 1000)

# From datetime object
dt = datetime(2024, 10, 19, 10, 30, 0)
timestamp_ms = int(dt.timestamp() * 1000)
```

#### 2. Event Types

| Event | When to Use | Weight in Training |
|-------|-------------|-------------------|
| `view` | User viewed product page | Low (implicit signal) |
| `add` | Added to cart/wishlist | Medium (intent signal) |
| `purchase` | Completed purchase | High (explicit positive) |

**Be consistent**: Choose one spelling and stick with it:
- Use `view` not `click`, `impression`, or `pageview`
- Use `add` not `add_to_cart`, `addtocart`, or `wishlist`
- Use `purchase` not `buy`, `order`, `transaction`, or `checkout`

#### 3. User IDs
- **Persistent**: Same user = same ID across sessions
- **Handle anonymous users**: Use session IDs for guests
- **Privacy**: Hash or pseudonymize if needed

```python
# Hashing user IDs for privacy
import hashlib

def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]

interactions = interactions.with_columns(
    pl.col("user_id").map_elements(hash_user_id, return_dtype=pl.Utf8)
)
```

#### 4. Data Quality

**Filter out**:
- Bot traffic
- Test accounts
- Internal employee interactions
- Duplicate events (same user, item, timestamp)

**Example cleaning**:
```python
# Remove duplicates
interactions = interactions.unique(subset=["user_id", "item_id", "timestamp"])

# Filter out test users
interactions = interactions.filter(~pl.col("user_id").str.starts_with("test_"))

# Remove items not in catalog
catalog_items = catalog["item_id"].to_list()
interactions = interactions.filter(pl.col("item_id").is_in(catalog_items))

# Keep only recent interactions (last 90 days)
cutoff = int((time.time() - 90*24*3600) * 1000)
interactions = interactions.filter(pl.col("timestamp") >= cutoff)
```

### Creating Interactions from Your Data

#### From Web Analytics (Google Analytics)

```python
import polars as pl
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest

# Initialize client
client = BetaAnalyticsDataClient()

# Run report
request = RunReportRequest(
    property=f"properties/{PROPERTY_ID}",
    date_ranges=[{"start_date": "90daysAgo", "end_date": "today"}],
    dimensions=["customUser:userId", "itemId", "eventName"],
    metrics=["eventCount"],
)
response = client.run_report(request)

# Transform to interactions
interactions_data = []
for row in response.rows:
    user_id = row.dimension_values[0].value
    item_id = row.dimension_values[1].value
    event = row.dimension_values[2].value
    
    # Map GA events to pocket-recs events
    if event == "page_view":
        event = "view"
    elif event == "add_to_cart":
        event = "add"
    elif event == "purchase":
        event = "purchase"
    else:
        continue
    
    interactions_data.append({
        "user_id": user_id,
        "item_id": item_id,
        "timestamp": int(time.time() * 1000),  # You'll need actual timestamps
        "event": event
    })

interactions = pl.DataFrame(interactions_data)
interactions.write_parquet("interactions.parquet")
```

#### From E-commerce Database

```python
import polars as pl
import psycopg2

conn = psycopg2.connect("postgresql://user:pass@localhost/db")

# Collect different event types
queries = {
    "view": """
        SELECT 
            user_id,
            product_id as item_id,
            EXTRACT(EPOCH FROM viewed_at) * 1000 as timestamp,
            'view' as event,
            brand,
            1 as quantity,
            price
        FROM product_views
        WHERE viewed_at >= NOW() - INTERVAL '90 days'
    """,
    "add": """
        SELECT 
            user_id,
            product_id as item_id,
            EXTRACT(EPOCH FROM added_at) * 1000 as timestamp,
            'add' as event,
            brand,
            quantity,
            price
        FROM cart_additions
        WHERE added_at >= NOW() - INTERVAL '90 days'
    """,
    "purchase": """
        SELECT 
            user_id,
            product_id as item_id,
            EXTRACT(EPOCH FROM purchased_at) * 1000 as timestamp,
            'purchase' as event,
            brand,
            quantity,
            price
        FROM order_items
        WHERE purchased_at >= NOW() - INTERVAL '90 days'
    """
}

# Combine all events
dfs = []
for event_type, query in queries.items():
    df = pl.read_database(query, conn)
    dfs.append(df)

interactions = pl.concat(dfs)

# Sort by timestamp
interactions = interactions.sort("timestamp")

interactions.write_parquet("interactions.parquet")
```

#### From Log Files

```python
import polars as pl
import json

# Parse JSON logs
events = []
with open("application.log", "r") as f:
    for line in f:
        try:
            log = json.loads(line)
            if log.get("event_type") in ["view", "add", "purchase"]:
                events.append({
                    "user_id": log["user_id"],
                    "item_id": log["item_id"],
                    "timestamp": log["timestamp"],
                    "event": log["event_type"],
                })
        except:
            continue

interactions = pl.DataFrame(events)
interactions.write_parquet("interactions.parquet")
```

## Data Quality Checks

### Validation Script

```python
import polars as pl

def validate_data(catalog_path: str, interactions_path: str):
    """Validate catalog and interactions data."""
    
    # Load data
    catalog = pl.read_csv(catalog_path)
    interactions = pl.read_parquet(interactions_path)
    
    print("=" * 80)
    print("DATA VALIDATION REPORT")
    print("=" * 80)
    
    # Catalog checks
    print("\n[CATALOG]")
    print(f"  Total items: {len(catalog)}")
    print(f"  Required columns: {'item_id' in catalog.columns and 'title' in catalog.columns}")
    print(f"  Unique item_ids: {catalog['item_id'].n_unique()}")
    print(f"  Duplicate item_ids: {len(catalog) - catalog['item_id'].n_unique()}")
    print(f"  Items with brand: {catalog['brand'].null_count() if 'brand' in catalog.columns else 0}")
    print(f"  Items with category: {catalog['category'].null_count() if 'category' in catalog.columns else 0}")
    
    # Interactions checks
    print("\n[INTERACTIONS]")
    print(f"  Total interactions: {len(interactions)}")
    print(f"  Unique users: {interactions['user_id'].n_unique()}")
    print(f"  Unique items: {interactions['item_id'].n_unique()}")
    print(f"  Date range: {pl.from_epoch(interactions['timestamp'].min()/1000)} to {pl.from_epoch(interactions['timestamp'].max()/1000)}")
    print(f"  Event distribution:")
    for event, count in interactions.group_by("event").count().iter_rows():
        print(f"    {event}: {count}")
    
    # Data quality checks
    print("\n[QUALITY CHECKS]")
    
    # Check timestamp format (should be 13 digits for milliseconds)
    min_ts = interactions["timestamp"].min()
    if len(str(min_ts)) != 13:
        print(f"  WARNING: Timestamps don't look like milliseconds (got {len(str(min_ts))} digits)")
    else:
        print(f"  Timestamp format: OK")
    
    # Check for items in interactions but not in catalog
    catalog_items = set(catalog["item_id"].to_list())
    interaction_items = set(interactions["item_id"].to_list())
    missing_items = interaction_items - catalog_items
    print(f"  Items in interactions but not catalog: {len(missing_items)}")
    if missing_items:
        print(f"    Examples: {list(missing_items)[:5]}")
    
    # Check for cold items (in catalog but no interactions)
    cold_items = catalog_items - interaction_items
    print(f"  Cold items (no interactions): {len(cold_items)} ({len(cold_items)/len(catalog_items)*100:.1f}%)")
    
    # Check for sparsity
    total_possible = interactions["user_id"].n_unique() * catalog["item_id"].n_unique()
    sparsity = 1 - (len(interactions) / total_possible)
    print(f"  Data sparsity: {sparsity*100:.2f}%")
    
    # Recommendations
    print("\n[RECOMMENDATIONS]")
    if len(interactions) < 1000:
        print("  - Consider collecting more interaction data (target: 10K+)")
    if len(catalog) < 100:
        print("  - Small catalog may limit recommendation quality")
    if len(missing_items) > len(catalog_items) * 0.1:
        print("  - Many interactions reference missing items - check data pipeline")
    if sparsity > 0.999:
        print("  - Very sparse data - recommendations may be less personalized")

# Run validation
validate_data("catalog.csv", "interactions.parquet")
```

## Minimum Data Requirements

For good recommendation quality:

| Metric | Minimum | Recommended | Ideal |
|--------|---------|-------------|-------|
| Items | 100+ | 1,000+ | 10,000+ |
| Users | 50+ | 500+ | 10,000+ |
| Interactions | 1,000+ | 10,000+ | 100,000+ |
| Interactions/User | 5+ | 20+ | 50+ |
| Interactions/Item | 3+ | 10+ | 100+ |

## Common Data Issues

### Issue 1: Timestamps in Seconds

**Problem**: Using seconds instead of milliseconds

**Fix**:
```python
interactions = interactions.with_columns(
    (pl.col("timestamp") * 1000).alias("timestamp")
)
```

### Issue 2: Invalid Event Types

**Problem**: Event types not in ['view', 'add', 'purchase']

**Fix**:
```python
# Map custom events
event_mapping = {
    "click": "view",
    "pageview": "view",
    "add_to_cart": "add",
    "wishlist": "add",
    "order": "purchase",
    "buy": "purchase",
}

interactions = interactions.with_columns(
    pl.col("event").replace(event_mapping)
).filter(
    pl.col("event").is_in(["view", "add", "purchase"])
)
```

### Issue 3: Missing Items

**Problem**: Interactions reference items not in catalog

**Fix**:
```python
# Keep only interactions with catalog items
catalog_items = catalog["item_id"].to_list()
interactions = interactions.filter(
    pl.col("item_id").is_in(catalog_items)
)
```

## Next Steps

- **[Offline Training](04-offline-training.md)**: Train your model
- **[Configuration](07-configuration.md)**: Tune for your data
- **[Troubleshooting](11-troubleshooting.md)**: Common data issues

---

Good data is the foundation of good recommendations. Take time to prepare it properly!

