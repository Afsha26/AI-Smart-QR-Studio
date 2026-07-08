"""Quality analysis utilities for QR codes.

Provides pure-Python heuristics for contrast, module sizing, and logo impact.
These are not replacements for image-based analysis but give quick feedback
before rendering or scanning.
"""
from __future__ import annotations
from typing import Dict, Optional


def analyze_contrast(fg: str, bg: str) -> Dict[str, str]:
    """Analyze simple color contrast between two hex colors.

    Returns a result with 'contrast' key: 'good' | 'poor' | 'unknown'.
    """
    try:
        def hex_to_rgb(h: str):
            h = h.lstrip('#')
            if len(h) == 3:
                h = ''.join([c*2 for c in h])
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        r1, g1, b1 = hex_to_rgb(fg)
        r2, g2, b2 = hex_to_rgb(bg)
        # relative luminance
        def lum(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        L1 = 0.2126 * lum(r1) + 0.7152 * lum(g1) + 0.0722 * lum(b1)
        L2 = 0.2126 * lum(r2) + 0.7152 * lum(g2) + 0.0722 * lum(b2)
        cr = (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05)
        # simple thresholds
        if cr >= 4.5:
            return {'contrast': 'good', 'ratio': f'{cr:.2f}'}
        if cr >= 3.0:
            return {'contrast': 'adequate', 'ratio': f'{cr:.2f}'}
        return {'contrast': 'poor', 'ratio': f'{cr:.2f}'}
    except Exception:
        return {'contrast': 'unknown', 'ratio': '0'}


def estimate_module_size(payload_length: int, canvas_px: int) -> Dict[str, object]:
    """Estimate module (square) size recommendations.

    This is heuristic: more data requires more modules at the QR version level.
    For quick feedback, we measure payload length vs canvas size.
    """
    # Very rough: more bytes -> more modules needed
    if canvas_px <= 0:
        canvas_px = 256
    modules = max(21, min(177, int((payload_length / 20) + 21)))
    module_px = canvas_px / modules
    recommendation = 'ok' if module_px >= 4 else 'increase_size_or_error_correction'
    return {'modules': modules, 'module_px': round(module_px, 2), 'recommendation': recommendation}


def assess_logo_impact(logo_bytes: Optional[bytes]) -> Dict[str, object]:
    """Estimate how much a logo will impact scanability.

    Simple heuristic: if a logo is present, recommend size limits.
    """
    if not logo_bytes:
        return {'impact': 'none', 'recommended_logo_pct': 0}
    # recommend logo occupy no more than 15-20% of QR width
    return {'impact': 'present', 'recommended_logo_pct': 18}


def analyze_quality(payload: str, options: Dict[str, object]) -> Dict[str, object]:
    """Combined quality analysis wrapper used by routers.

    `options` may include color keys `fg`, `bg`, `size`, and `logo` metadata.
    """
    fg = options.get('fg') or '#000000'
    bg = options.get('bg') or '#ffffff'
    size = int(options.get('size') or 512)
    logo = options.get('logo')

    contrast = analyze_contrast(fg, bg)
    module = estimate_module_size(len(payload or ''), size)
    logo_imp = assess_logo_impact(logo)

    score = 80
    if contrast.get('contrast') == 'poor':
        score -= 25
    if module.get('recommendation') != 'ok':
        score -= 10
    if logo_imp.get('impact') == 'present':
        score -= 5

    return {
        'contrast': contrast,
        'module': module,
        'logo': logo_imp,
        'score': max(0, score),
        'notes': 'Heuristic analysis. Replace with image-based checks for production.'
    }
