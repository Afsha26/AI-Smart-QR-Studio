"""Service-layer wrapper for QR quality analysis."""

from __future__ import annotations

from backend.services import quality_service


async def analyze_quality(payload: str, options: dict | None = None) -> dict:
    """Delegate QR quality analysis to the dedicated quality service."""
    return await quality_service.analyze_quality(payload, options or {})
