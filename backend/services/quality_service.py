"""Quality analysis utilities for QR codes.

This module contains the reusable heuristics for contrast, module sizing,
and logo impact. It is kept independent so future image-based analysis can
be added without changing the router or service layer.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Convert a hex color string to RGB values."""
    cleaned = value.lstrip('#')
    if len(cleaned) == 3:
        cleaned = ''.join(char * 2 for char in cleaned)
    if len(cleaned) != 6:
        raise ValueError('Invalid color format')
    return tuple(int(cleaned[index:index + 2], 16) for index in (0, 2, 4))


def _relative_luminance(color: str) -> float:
    """Calculate relative luminance for a hex color."""
    red, green, blue = _hex_to_rgb(color)
    channels = [red / 255.0, green / 255.0, blue / 255.0]
    corrected = []
    for channel in channels:
        corrected.append(channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * corrected[0] + 0.7152 * corrected[1] + 0.0722 * corrected[2]


def analyze_contrast(fg: str, bg: str) -> Dict[str, str]:
    """Analyze the contrast ratio between foreground and background colors."""
    try:
        fg_luminance = _relative_luminance(fg)
        bg_luminance = _relative_luminance(bg)
        ratio = (max(fg_luminance, bg_luminance) + 0.05) / (min(fg_luminance, bg_luminance) + 0.05)
        if ratio >= 7.0:
            status = 'Excellent'
        elif ratio >= 4.5:
            status = 'Good'
        elif ratio >= 3.0:
            status = 'Fair'
        else:
            status = 'Poor'
        return {'status': status, 'ratio': f'{ratio:.1f}:1'}
    except Exception:
        return {'status': 'Unknown', 'ratio': '0:1'}


def estimate_module_size(payload_length: int, canvas_px: int) -> Dict[str, Any]:
    """Estimate the module size needed for reliable scanning."""
    if canvas_px <= 0:
        canvas_px = 256
    modules = max(21, min(177, int((payload_length / 20) + 21)))
    module_px = canvas_px / modules
    recommended_minimum = 6 if payload_length > 300 else 4
    if module_px >= 8:
        status = 'Excellent'
    elif module_px >= recommended_minimum:
        status = 'Good'
    else:
        status = 'Too Small'
    return {
        'status': status,
        'module_px': round(module_px, 2),
        'recommended_minimum': recommended_minimum,
    }


def assess_logo_impact(logo: Optional[Any], logo_pct: Optional[float] = None) -> Dict[str, Any]:
    """Assess how a logo may affect QR scan reliability."""
    if not logo:
        return {'status': 'None', 'recommended_logo_pct': 0}

    if logo_pct is None:
        if isinstance(logo, dict):
            logo_pct = logo.get('size_pct') or logo.get('size')
        elif isinstance(logo, (int, float)):
            logo_pct = float(logo)
        else:
            logo_pct = 0

    recommended_logo_pct = 18
    if logo_pct is None or logo_pct <= 0:
        status = 'Safe'
    elif logo_pct > recommended_logo_pct:
        status = 'High Risk'
    elif logo_pct > recommended_logo_pct * 0.75:
        status = 'Medium Risk'
    else:
        status = 'Safe'

    return {'status': status, 'recommended_logo_pct': recommended_logo_pct}


def calculate_overall_score(contrast: Dict[str, str], module: Dict[str, Any], logo: Dict[str, Any]) -> int:
    """Calculate an overall QR scan quality score from 0 to 100."""
    score = 100
    contrast_status = contrast.get('status', 'Unknown')
    module_status = module.get('status', 'Good')
    logo_status = logo.get('status', 'None')

    if contrast_status == 'Poor':
        score -= 35
    elif contrast_status == 'Fair':
        score -= 20
    elif contrast_status == 'Good':
        score -= 8
    elif contrast_status == 'Unknown':
        score -= 15

    if module_status == 'Too Small':
        score -= 15
    elif module_status == 'Good':
        score -= 5

    if logo_status == 'Medium Risk':
        score -= 8
    elif logo_status == 'High Risk':
        score -= 16

    return max(0, min(100, round(score)))


def generate_recommendations(contrast: Dict[str, str], module: Dict[str, Any], logo: Dict[str, Any]) -> list[str]:
    """Generate actionable recommendations based on scan heuristics."""
    recommendations: list[str] = []

    if contrast.get('status') in {'Poor', 'Fair', 'Unknown'}:
        recommendations.append('Increase contrast between foreground and background colors.')
    if module.get('status') == 'Too Small':
        recommendations.append('Increase QR code size.')
    if logo.get('status') in {'Medium Risk', 'High Risk'}:
        recommendations.append('Reduce logo size below 18%.')

    if not recommendations:
        recommendations.append('This QR code should scan reliably.')
    return recommendations


async def analyze_quality(payload: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze QR payload and design options for scan quality."""
    await asyncio.sleep(0.02)

    fg = options.get('fg') or '#000000'
    bg = options.get('bg') or '#ffffff'
    size = int(options.get('size') or 512)
    logo = options.get('logo')
    logo_pct = options.get('logo_pct')

    contrast = analyze_contrast(fg, bg)
    module = estimate_module_size(len(payload or ''), size)
    logo_result = assess_logo_impact(logo, logo_pct)
    score = calculate_overall_score(contrast, module, logo_result)

    return {
        'score': score,
        'contrast': contrast,
        'module': module,
        'logo': logo_result,
        'recommendations': generate_recommendations(contrast, module, logo_result),
    }
