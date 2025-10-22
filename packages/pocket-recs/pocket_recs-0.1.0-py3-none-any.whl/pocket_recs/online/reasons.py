"""Reason code generation for explainability."""

from __future__ import annotations

from typing import List


def generate_reason_codes(
    has_covis: bool,
    ann_score: float,
    brand_boost: float,
    covis_threshold: float = 0.1,
    ann_threshold: float = 0.5,
    brand_threshold: float = 0.05,
) -> List[str]:
    """
    Generate human-readable reason codes for a recommendation.

    Args:
        has_covis: Whether item appears in co-visitation
        ann_score: ANN similarity score
        brand_boost: Brand popularity boost value
        covis_threshold: Threshold for co-visitation reason
        ann_threshold: Threshold for semantic match reason
        brand_threshold: Threshold for brand-pop reason

    Returns:
        List of reason codes
    """
    reasons: List[str] = []

    if has_covis and covis_threshold > 0:
        reasons.append("co-visitation")

    if ann_score >= ann_threshold:
        reasons.append("semantic-match")

    if brand_boost >= brand_threshold:
        reasons.append("brand-popular")

    if not reasons:
        reasons.append("baseline")

    return reasons

