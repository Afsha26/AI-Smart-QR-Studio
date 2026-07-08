"""AI service stubs.

Replace these stubs with real integrations to your chosen AI provider (Gemini, OpenAI, etc.).
Keep I/O and network calls here so routers stay thin.
"""
import asyncio


async def generate_theme(prompt: str) -> dict:
    """Generate a theme from prompt. Return a dict describing colors, fonts, and layout hints.

    NOTE: This is a stub returning a deterministic sample. Replace with actual API calls.
    """
    await asyncio.sleep(0.05)
    return {
        'theme': {
            'primary': '#4F46E5',
            'secondary': '#7C3AED',
            'bg': '#F8FAFC',
            'fg': '#0F172A'
        },
        'notes': f'Sample theme generated for prompt: {prompt[:80]}'
    }


async def generate_content(prompt: str, type_hint: str | None = None) -> dict:
    """Generate copy or structured content. Returns title/tagline/cta/content.

    NOTE: Stubbed for tests and local development.
    """
    await asyncio.sleep(0.05)
    return {
        'title': 'Sample QR Title',
        'tagline': 'A short tagline generated from AI',
        'cta': 'Scan to learn more',
        'content': f'Generated content for type={type_hint} prompt={prompt[:120]}'
    }
