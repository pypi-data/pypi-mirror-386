# API Guide

This guide covers deploying and using Pocket-Recs as a REST API service.

## Overview

Pocket-Recs includes a production-ready FastAPI server that provides:

- **RESTful endpoints** for recommendations
- **Interactive documentation** (Swagger UI)
- **Health and readiness checks**
- **Request validation** (Pydantic models)
- **CORS support**
- **Error handling**

## Quick Start

### Start the Server

**Using CLI**:
```bash
pocket-recs serve artifacts/ catalog.csv --port 8000
```

**Using Python**:
```python
from pocket_recs.api import create_app
import uvicorn

app = create_app("artifacts/", "catalog.csv")
uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Access Documentation**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Health Checks

#### GET /healthz

Health check endpoint for load balancers.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": 1697123456.789
}
```

**Example**:
```bash
curl http://localhost:8000/healthz
```

#### GET /readyz

Readiness check to verify model is loaded.

**Response**:
```json
{
  "ready": true,
  "model_loaded": true,
  "artifact_version": "0.1.0"
}
```

### Recommendations

#### POST /v1/recommend

Get personalized recommendations for a user.

**Request Body**:
```json
{
  "user_id": "user_12345",
  "k": 10,
  "recent": [
    {
      "user_id": "user_12345",
      "item_id": "item_001",
      "timestamp": 1697123456000,
      "event": "view"
    }
  ],
  "brand": "Nike",
  "exclusions": ["item_001"]
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | User identifier |
| `k` | integer | No | Number of recommendations (1-100, default: 20) |
| `recent` | array | No | Recent user interactions |
| `brand` | string | No | Filter by brand |
| `exclusions` | array | No | Item IDs to exclude |

**Response**:
```json
{
  "items": [
    {
      "item_id": "item_123",
      "score": 0.87,
      "reasons": ["semantic", "brand-popular"],
      "rank": 1
    },
    {
      "item_id": "item_456",
      "score": 0.82,
      "reasons": ["co-visited"],
      "rank": 2
    }
  ],
  "artifact_version": "0.1.0",
  "metadata": {
    "total_candidates": 150,
    "covis_candidates": 40,
    "brand_candidates": 50,
    "ann_candidates": 80
  }
}
```

**Example with curl**:
```bash
curl -X POST "http://localhost:8000/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "k": 10,
    "recent": [
      {
        "user_id": "user_123",
        "item_id": "item_5",
        "timestamp": 1700000000000,
        "event": "view"
      }
    ]
  }'
```

**Example with Python requests**:
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/recommend",
    json={
        "user_id": "user_123",
        "k": 10,
        "recent": [
            {
                "user_id": "user_123",
                "item_id": "item_5",
                "timestamp": 1700000000000,
                "event": "view"
            }
        ]
    }
)

recommendations = response.json()
print(recommendations["items"])
```

**Example with JavaScript/TypeScript**:
```javascript
const response = await fetch('http://localhost:8000/v1/recommend', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'user_123',
    k: 10,
    recent: [
      {
        user_id: 'user_123',
        item_id: 'item_5',
        timestamp: 1700000000000,
        event: 'view'
      }
    ]
  })
});

const recommendations = await response.json();
console.log(recommendations.items);
```

## Client Libraries

### Python Client

```python
import requests
from typing import List, Dict, Optional

class PocketRecsClient:
    """Python client for Pocket-Recs API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
    
    def recommend(
        self,
        user_id: str,
        k: int = 10,
        recent: Optional[List[Dict]] = None,
        brand: Optional[str] = None,
        exclusions: Optional[List[str]] = None
    ) -> Dict:
        """Get recommendations for a user."""
        
        payload = {
            "user_id": user_id,
            "k": k,
            "recent": recent or [],
        }
        
        if brand:
            payload["brand"] = brand
        if exclusions:
            payload["exclusions"] = exclusions
        
        response = requests.post(
            f"{self.base_url}/v1/recommend",
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> bool:
        """Check if service is healthy."""
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=2)
            return response.status_code == 200
        except:
            return False

# Usage
client = PocketRecsClient("http://localhost:8000")

recommendations = client.recommend(
    user_id="user_123",
    k=10,
    recent=[
        {
            "user_id": "user_123",
            "item_id": "item_5",
            "timestamp": 1700000000000,
            "event": "view"
        }
    ]
)

print(f"Got {len(recommendations['items'])} recommendations")
```

### JavaScript/TypeScript Client

```typescript
interface Interaction {
  user_id: string;
  item_id: string;
  timestamp: number;
  event: 'view' | 'add' | 'purchase';
}

interface RecommendRequest {
  user_id: string;
  k?: number;
  recent?: Interaction[];
  brand?: string;
  exclusions?: string[];
}

interface RecommendItem {
  item_id: string;
  score: number;
  reasons: string[];
  rank: number;
}

interface RecommendResponse {
  items: RecommendItem[];
  artifact_version: string;
  metadata: Record<string, any>;
}

class PocketRecsClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  async recommend(request: RecommendRequest): Promise<RecommendResponse> {
    const response = await fetch(`${this.baseUrl}/v1/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/healthz`);
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Usage
const client = new PocketRecsClient('http://localhost:8000');

const recommendations = await client.recommend({
  user_id: 'user_123',
  k: 10,
  recent: [
    {
      user_id: 'user_123',
      item_id: 'item_5',
      timestamp: Date.now(),
      event: 'view'
    }
  ]
});

console.log(`Got ${recommendations.items.length} recommendations`);
```

## Production Deployment

### Using Uvicorn (Development)

```bash
uvicorn pocket_recs.api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Using Gunicorn (Production)

```bash
gunicorn pocket_recs.api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

**Configuration**:
- `--workers`: Number of worker processes (usually 2-4 per CPU core)
- `--worker-class`: Must be `uvicorn.workers.UvicornWorker`
- `--timeout`: Request timeout in seconds
- `--bind`: Host and port to bind to

### Docker Deployment

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn uvicorn[standard]

# Copy application
COPY . .

# Copy artifacts
COPY artifacts/ ./artifacts/
COPY catalog.csv ./catalog.csv

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1

# Run application
CMD ["gunicorn", "pocket_recs.api.app:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120"]
```

**Build and run**:
```bash
# Build image
docker build -t pocket-recs-api .

# Run container
docker run -d \
  -p 8000:8000 \
  --name pocket-recs-api \
  pocket-recs-api

# Check logs
docker logs -f pocket-recs-api

# Test
curl http://localhost:8000/healthz
```

### Docker Compose

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=info
    volumes:
      - ./artifacts:/app/artifacts:ro
      - ./catalog.csv:/app/catalog.csv:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

**Usage**:
```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### Kubernetes Deployment

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pocket-recs-api
  labels:
    app: pocket-recs-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pocket-recs-api
  template:
    metadata:
      labels:
        app: pocket-recs-api
    spec:
      containers:
      - name: api
        image: pocket-recs-api:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: LOG_LEVEL
          value: "info"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 5
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: artifacts
          mountPath: /app/artifacts
          readOnly: true
        - name: catalog
          mountPath: /app/catalog.csv
          subPath: catalog.csv
          readOnly: true
      volumes:
      - name: artifacts
        persistentVolumeClaim:
          claimName: artifacts-pvc
      - name: catalog
        configMap:
          name: catalog-config

---
apiVersion: v1
kind: Service
metadata:
  name: pocket-recs-api
spec:
  selector:
    app: pocket-recs-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Apply**:
```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl get services
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ARTIFACTS_DIR` | Path to artifacts directory | `./artifacts` |
| `CATALOG_PATH` | Path to catalog CSV | `./catalog.csv` |
| `HOST` | API host | `0.0.0.0` |
| `PORT` | API port | `8000` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` |
| `LOG_LEVEL` | Logging level | `info` |

**Example**:
```bash
export ARTIFACTS_DIR=/data/artifacts
export CATALOG_PATH=/data/catalog.csv
export PORT=8080
export CORS_ORIGINS="https://example.com,https://app.example.com"

pocket-recs serve $ARTIFACTS_DIR $CATALOG_PATH --port $PORT
```

## Monitoring

### Logging

The API logs to stdout in JSON format:

```json
{
  "timestamp": "2024-10-19T10:30:00",
  "level": "INFO",
  "message": "Recommendation request",
  "user_id": "user_123",
  "k": 10,
  "latency_ms": 23.5
}
```

### Prometheus Metrics (Advanced)

Add Prometheus instrumentation:

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# Define metrics
request_count = Counter(
    'recommendation_requests_total',
    'Total recommendation requests',
    ['user_id']
)

request_duration = Histogram(
    'recommendation_duration_seconds',
    'Recommendation request duration'
)

# Add to API
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

# Instrument endpoints
@request_duration.time()
def recommend(request: RecommendRequest):
    request_count.labels(user_id=request.user_id).inc()
    # ... recommendation logic
```

## Security

### API Key Authentication

Add API key authentication:

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = "your-secret-key"
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/v1/recommend")
async def recommend(
    request: RecommendRequest,
    api_key: str = Security(verify_api_key)
):
    # ... recommendation logic
```

### Rate Limiting

Add rate limiting with slowapi:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/v1/recommend")
@limiter.limit("100/minute")
async def recommend(request: Request, rec_request: RecommendRequest):
    # ... recommendation logic
```

### CORS Configuration

Configure CORS for frontend access:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],  # Production domains
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

## Error Handling

The API returns standard HTTP status codes:

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Recommendation generated |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Endpoint doesn't exist |
| 422 | Validation Error | Invalid request body |
| 500 | Server Error | Internal error |

**Error response format**:
```json
{
  "detail": "Invalid parameter: k must be between 1 and 100"
}
```

## Performance Tuning

### Worker Configuration

For high throughput:
```bash
# More workers = higher throughput
gunicorn app:app \
  --workers 8 \
  --worker-connections 1000 \
  --timeout 120
```

For low latency:
```bash
# Fewer workers = lower memory, better latency
gunicorn app:app \
  --workers 2 \
  --preload  # Preload model before forking
```

### Load Testing

Test API performance:

```bash
# Install Apache Bench
apt-get install apache2-utils

# Test endpoint
ab -n 1000 -c 10 \
  -p payload.json \
  -T application/json \
  http://localhost:8000/v1/recommend
```

**payload.json**:
```json
{
  "user_id": "test_user",
  "k": 10,
  "recent": []
}
```

## Next Steps

- **[Configuration](07-configuration.md)**: Tune API performance
- **[Production Deployment](09-production-deployment.md)**: Advanced deployment strategies
- **[Troubleshooting](11-troubleshooting.md)**: Common API issues

---

Deploy your recommendation API with confidence!

