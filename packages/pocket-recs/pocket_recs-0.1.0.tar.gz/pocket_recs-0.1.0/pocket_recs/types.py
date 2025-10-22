"""Type definitions and data contracts for pocket-recs."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

EventType = Literal["view", "add", "purchase"]


class CatalogItem(BaseModel):
    """Product catalog item schema."""

    item_id: str = Field(description="Unique item identifier")
    brand: Optional[str] = Field(default=None, description="Brand name")
    category: Optional[str] = Field(default=None, description="Product category")
    title: str = Field(description="Product title")
    short_desc: Optional[str] = Field(default=None, description="Short description")
    price: Optional[float] = Field(default=None, description="Product price")
    in_stock: Optional[bool] = Field(default=True, description="Stock availability")


class Interaction(BaseModel):
    """User-item interaction event."""

    user_id: str = Field(description="User identifier")
    item_id: str = Field(description="Item identifier")
    brand: Optional[str] = Field(default=None, description="Brand at interaction time")
    timestamp: int = Field(description="Unix timestamp in milliseconds")
    quantity: Optional[int] = Field(default=1, description="Quantity (for purchases)")
    price: Optional[float] = Field(default=None, description="Price at interaction time")
    event: EventType = Field(default="view", description="Event type")


class RecommendRequest(BaseModel):
    """Request schema for recommendations."""

    user_id: str = Field(description="User identifier")
    brand: Optional[str] = Field(default=None, description="Filter by brand")
    k: int = Field(default=20, ge=1, le=100, description="Number of recommendations")
    recent: List[Interaction] = Field(
        default_factory=list, description="Recent user interactions"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional filters"
    )
    exclusions: Optional[List[str]] = Field(
        default=None, description="Items to exclude"
    )


class RecommendItem(BaseModel):
    """Single recommended item with metadata."""

    item_id: str = Field(description="Item identifier")
    score: float = Field(description="Recommendation score")
    reasons: List[str] = Field(description="Reason codes for recommendation")
    rank: int = Field(description="Rank position in results")


class RecommendResponse(BaseModel):
    """Response schema for recommendations."""

    request_id: str = Field(description="Unique request identifier")
    items: List[RecommendItem] = Field(description="Recommended items")
    artifact_version: str = Field(description="Model artifact version")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional response metadata"
    )

