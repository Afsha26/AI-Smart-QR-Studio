"""Validator service: URL sanitization and policy checks.

This module provides reusable validation functions for URLs and domains.
It is intentionally light-weight — extend with allow/deny lists, whitelists,
and safety checks as needed.
"""
from __future__ import annotations
from typing import Dict, List, Optional
from urllib.parse import urlparse, urlunparse
import re


def _normalize_url(url: str) -> Optional[str]:
    """Normalize a URL by ensuring a scheme and removing whitespace.

    Returns normalized URL or None if input is clearly invalid.
    """
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    # add scheme if missing
    if not re.match(r'^https?:\/\/', url, flags=re.I):
        url = 'http://' + url
    try:
        p = urlparse(url)
        if not p.netloc:
            return None
        # rebuild to a consistent representation
        normalized = urlunparse((p.scheme.lower(), p.netloc, p.path or '', p.params or '', p.query or '', p.fragment or ''))
        return normalized
    except Exception:
        return None


async def validate_url(url: str) -> Dict[str, any]:
    """Asynchronously validate a URL and return a structured result.

    Result format:
      {
        'valid': bool,
        'normalized': Optional[str],
        'issues': List[str]
      }
    """
    normalized = _normalize_url(url)
    issues: List[str] = []
    if not normalized:
        issues.append('invalid_url')
        return {'valid': False, 'normalized': None, 'issues': issues}

    # Basic policy checks (expand as needed)
    parsed = urlparse(normalized)
    hostname = parsed.hostname or ''
    # reject localhost in production via env (not enforced here)
    if hostname in ('localhost', '127.0.0.1'):
        issues.append('local_host')

    # block obvious data: URIs like javascript: or data:
    if parsed.scheme not in ('http', 'https'):
        issues.append('unsupported_scheme')

    valid = len(issues) == 0
    return {'valid': valid, 'normalized': normalized, 'issues': issues}
