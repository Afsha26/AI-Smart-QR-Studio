from urllib.parse import urlparse


def is_valid_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)
    except Exception:
        return False


def safe_getenv(name: str, default: str = '') -> str:
    from os import getenv
    return getenv(name, default)
