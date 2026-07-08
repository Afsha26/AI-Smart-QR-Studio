"""QR rendering utilities.

Provides async functions to render QR codes to SVG or PNG bytes. Uses
`segno` when available for high-quality QR generation. PNG rendering uses
Pillow if present; otherwise PNG rendering via segno (which may also use
Pillow under the hood).

All heavy CPU or IO-bound operations are executed in a threadpool to avoid
blocking the event loop.
"""
from __future__ import annotations
from typing import Tuple, Optional
import asyncio
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

try:
    import segno
    _HAS_SEGNO = True
except Exception:
    segno = None
    _HAS_SEGNO = False


async def _run_blocking(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


async def generate_svg(payload: str, border: int = 4, scale: int = 1) -> bytes:
    """Generate SVG bytes for the given payload.

    Returns raw bytes of the SVG document (UTF-8 encoded).
    """
    if not _HAS_SEGNO:
        raise RuntimeError('segno is required for SVG generation. Install segno in the backend environment.')

    def _make():
        qr = segno.make(payload)
        out = BytesIO()
        qr.save(out, kind='svg', xmldecl=True, scale=scale, border=border)
        return out.getvalue()

    return await _run_blocking(_make)


async def generate_png(payload: str, scale: int = 4, border: int = 4) -> bytes:
    """Generate PNG bytes for the given payload.

    This uses segno's PNG output which will use Pillow if available. If
    Pillow is not installed, segno still writes PNG via its own routine.
    """
    if not _HAS_SEGNO:
        raise RuntimeError('segno is required for PNG generation. Install segno in the backend environment.')

    def _make():
        qr = segno.make(payload)
        out = BytesIO()
        qr.save(out, kind='png', scale=scale, border=border)
        return out.getvalue()

    return await _run_blocking(_make)


async def render(payload: str, fmt: str = 'png', options: Optional[dict] = None) -> Tuple[bytes, str]:
    """Render payload into (bytes, mime_type) depending on `fmt`.

    Supported formats: 'png', 'svg'.
    """
    fmt = (fmt or 'png').lower()
    options = options or {}
    if fmt == 'svg':
        data = await generate_svg(payload, border=int(options.get('border', 4)), scale=int(options.get('scale', 1)))
        return data, 'image/svg+xml'
    if fmt == 'png':
        data = await generate_png(payload, scale=int(options.get('scale', 4)), border=int(options.get('border', 4)))
        return data, 'image/png'
    raise ValueError(f'Unsupported format: {fmt}')
