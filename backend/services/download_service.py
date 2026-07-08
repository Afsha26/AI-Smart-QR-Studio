"""Download/render service stub.

This module should render QR codes server-side (SVG/PNG) and return bytes + mime type.
For now it returns a tiny placeholder PNG or simple SVG for demos.
"""
import asyncio
import base64

SAMPLE_SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="100%" height="100%" fill="#fff"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#000">QR</text></svg>'''


async def render_download(payload: str, fmt: str, options: dict) -> tuple[bytes, str]:
    await asyncio.sleep(0.02)
    if fmt == 'svg':
        return (SAMPLE_SVG, 'image/svg+xml')
    # return tiny PNG via data URI decode (transparent 1x1 PNG)
    # For demo, encode a very small 1x1 PNG (not actually a QR) — replace with real render
    tiny_png_b64 = (
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='
    )
    return (base64.b64decode(tiny_png_b64), 'image/png')
