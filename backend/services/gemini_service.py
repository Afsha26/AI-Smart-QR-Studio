"""Minimal Gemini-style AI service wrapper.

This module provides a small async wrapper to call an external AI provider
via HTTP. It prefers environment configuration and falls back to a local
stubbed response when credentials are not present (useful for development).

Replace or extend with a proper SDK integration when available.
"""
from __future__ import annotations
import os
from typing import Any, Dict
import asyncio

import httpx

GEMINI_API_URL = os.getenv('GEMINI_API_URL')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


async def generate_text(prompt: str, max_tokens: int = 256) -> Dict[str, Any]:
    """Generate text from prompt using the configured AI provider.

    If `GEMINI_API_URL` and `GEMINI_API_KEY` are set, an async HTTP POST will
    be performed. Otherwise this function returns a deterministic stub.

    Returns a dictionary with at least a `text` key.
    """
    if not prompt:
        raise ValueError('prompt is required')

    # If not configured, return a fast local stub for development
    if not (GEMINI_API_URL and GEMINI_API_KEY):
        await asyncio.sleep(0.01)
        return {
            'text': f'(stub) Generated text for prompt: {prompt[:120]}',
            'meta': {'stub': True}
        }

    # Real HTTP call path
    headers = {'Authorization': f'Bearer {GEMINI_API_KEY}', 'Content-Type': 'application/json'}
    payload = {'prompt': prompt, 'max_tokens': max_tokens}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(GEMINI_API_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        # Normalize response to expected shape
        return {'text': data.get('text') or data.get('output') or str(data), 'meta': data}
