"""Download and rendering service.

Renders genuine QR codes (PNG/SVG) using `backend.services.qr_service`.
"""
from typing import Tuple
from backend.services.qr_service import render as qr_render


async def render_download(payload: str, fmt: str, options: dict) -> Tuple[bytes, str]:
    """Render a QR code in the requested format (PNG or SVG) and return (bytes, mime_type)."""
    return await qr_render(payload, fmt, options or {})
