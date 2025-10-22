# Changelog

All notable changes to Pocket-Recs will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX

### Added
- Initial release of Pocket-Recs
- Two-tower retrieval architecture with ANN search (FAISS/HNSW)
- Co-visitation matrix with time decay
- Brand-popularity scoring with recency weighting
- LightGBM LambdaRank re-ranking (stub implementation)
- MMR diversification
- Text embeddings using sentence-transformers
- CPU-optimized inference
- FastAPI REST API server
- CLI tool for training and inference
- Comprehensive documentation and examples
- Test suite with pytest
- CI/CD pipeline with GitHub Actions
- Artifact versioning and manifest management
- Explainable recommendations with reason codes

### Features
- Support for catalogs up to 100k items
- 10-40ms p95 latency on modest hardware
- Configurable pipeline parameters
- Health and readiness endpoints for API
- Sample data generation utilities
- Parquet and CSV data formats

### Documentation
- Comprehensive README with quick start
- Contributing guidelines
- Code of conduct
- Example scripts and sample data
- API documentation (via FastAPI /docs)

## [Unreleased]

### Planned
- Item2Vec/SPPMI collaborative embeddings
- Cross-encoder reranking with ONNX quantization
- Sequential transformer features (SASRec/BERT4Rec)
- Offline evaluation metrics (NDCG@K, Recall@K, MAP@K)
- A/B testing utilities
- DiskANN support for >1M items
- OpenVINO INT8 quantization
- Streamlit demo UI
- Docker Compose deployment templates

