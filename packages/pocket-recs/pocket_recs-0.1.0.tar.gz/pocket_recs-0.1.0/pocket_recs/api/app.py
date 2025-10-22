"""FastAPI application for recommendation API."""

from __future__ import annotations

import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pocket_recs.config import RecommenderConfig
from pocket_recs.online.recommender import Recommender
from pocket_recs.types import RecommendRequest, RecommendResponse


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: float


class ReadyResponse(BaseModel):
    """Readiness check response."""

    ready: bool
    artifact_version: str


def create_app(
    artifacts_dir: str,
    catalog_path: str,
    config: Optional[RecommenderConfig] = None,
) -> FastAPI:
    """
    Create FastAPI application instance.

    Args:
        artifacts_dir: Path to model artifacts
        catalog_path: Path to catalog CSV
        config: Optional recommender configuration

    Returns:
        FastAPI application instance
    """
    app = FastAPI(
        title="Pocket Recs API",
        description="CPU-only hybrid recommendation system",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    try:
        recommender = Recommender(artifacts_dir, catalog_path, config)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize recommender: {e}")

    @app.get("/healthz", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            timestamp=time.time(),
        )

    @app.get("/readyz", response_model=ReadyResponse)
    async def readiness_check() -> ReadyResponse:
        """Readiness check endpoint."""
        return ReadyResponse(
            ready=True,
            artifact_version=recommender.manifest.version,
        )

    @app.post("/v1/recommend", response_model=RecommendResponse)
    async def recommend(request: RecommendRequest) -> RecommendResponse:
        """
        Get recommendations for a user.

        Args:
            request: Recommendation request

        Returns:
            Recommendation response with items
        """
        try:
            response = recommender.recommend(request)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Pocket Recs API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/healthz",
            "ready": "/readyz",
        }

    return app

