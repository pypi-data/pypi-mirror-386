FROM python:3.11-slim

LABEL maintainer="amjad@example.com"
LABEL description="Pocket-Recs: CPU-only hybrid recommender system"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir hnswlib fastapi uvicorn[standard]

COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["pocket-recs", "version"]

