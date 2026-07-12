"""Reusable validation helpers for the AI Smart QR Generator backend.

This module keeps the validation logic lightweight and modular so each QR type
can be validated independently or through a single dispatcher entrypoint.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

_EMAIL_REGEX = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", re.IGNORECASE)
_SUPPORTED_SOCIAL_PLATFORMS = {
    "instagram": r"^[a-z0-9._]{1,30}$",
    "facebook": r"^[a-z0-9.]{5,50}$",
    "x": r"^[a-z0-9_]{1,15}$",
    "twitter": r"^[a-z0-9_]{1,15}$",
    "linkedin": r"^[a-z0-9-]{3,100}$",
    "github": r"^[a-z0-9](?:[a-z0-9-]{0,38})$",
    "youtube": r"^[a-z0-9][a-z0-9-]{0,29}$",
}
_VALID_WIFI_ENCRYPTION = {"WPA", "WPA2", "WPA3", "WEP", "NOPASS"}


def _normalize_url(url: str) -> Tuple[Optional[str], List[str]]:
    """Normalize a URL and return the normalized value plus any issues."""
    issues: List[str] = []
    if not isinstance(url, str):
        return None, ["invalid_url"]

    value = url.strip()
    if not value:
        return None, ["invalid_url"]

    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value):
        scheme = value.split(":", 1)[0].lower()
        if scheme not in {"http", "https"}:
            return None, ["unsupported_scheme"]
        candidate = value
    else:
        candidate = f"http://{value}"

    try:
        parsed = urlparse(candidate)
    except Exception:
        return None, ["invalid_url"]

    if not parsed.netloc:
        return None, ["invalid_url"]

    hostname = parsed.hostname or ""
    if not re.fullmatch(r"[a-z0-9.-]+", hostname, re.IGNORECASE) or hostname.startswith(".") or hostname.endswith("."):
        return None, ["invalid_url"]

    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return None, ["local_host"]

    normalized = urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc,
            parsed.path or "",
            parsed.params or "",
            parsed.query or "",
            parsed.fragment or "",
        )
    )
    return normalized, issues


def _normalize_phone(phone: str) -> Optional[str]:
    """Normalize a phone number by removing spaces, brackets and hyphens."""
    if not isinstance(phone, str):
        return None

    value = phone.strip()
    if not value:
        return None

    if value.startswith("+"):
        if value.count("+") != 1:
            return None
        digits = re.sub(r"[\s\-\(\)]", "", value[1:])
        if not digits.isdigit():
            return None
        normalized = f"+{digits}"
    else:
        digits = re.sub(r"[\s\-\(\)]", "", value)
        if not digits.isdigit():
            return None
        normalized = digits

    if len(digits) < 8 or len(digits) > 15:
        return None

    return normalized


def _validate_text(text: str) -> Tuple[Optional[str], List[str]]:
    """Trim text and enforce the supported length limit."""
    issues: List[str] = []
    if not isinstance(text, str):
        return None, ["empty_text"]

    normalized = text.strip()
    if not normalized:
        issues.append("empty_text")
    elif len(normalized) > 3000:
        issues.append("text_too_long")

    return normalized or None, issues


def _validate_email_regex(email: str) -> Tuple[Optional[str], List[str]]:
    """Normalize an email address and validate it with a regular expression."""
    issues: List[str] = []
    if not isinstance(email, str):
        return None, ["invalid_email"]

    normalized = email.strip().lower()
    if not normalized or not _EMAIL_REGEX.fullmatch(normalized):
        issues.append("invalid_email")

    return normalized or None, issues


def _normalize_social_platform(platform: str) -> Optional[str]:
    """Normalize a supported social platform name to the canonical key."""
    if not isinstance(platform, str):
        return None

    normalized = platform.strip().lower()
    if normalized in _SUPPORTED_SOCIAL_PLATFORMS:
        return normalized
    return None


def _split_payload(value: str, separator: str = "|") -> List[str]:
    """Split a pipe-delimited payload into a list of fields."""
    if not isinstance(value, str):
        return []
    return [part.strip() for part in value.split(separator) if part.strip()]


async def validate_url(url: str) -> Dict[str, Any]:
    """Validate and normalize a URL for QR payload generation."""
    normalized, issues = _normalize_url(url)
    return {"valid": not issues, "normalized": normalized, "issues": issues}


async def validate_text(text: str) -> Dict[str, Any]:
    """Validate free-form text content and trim it for QR encoding."""
    normalized, issues = _validate_text(text)
    return {"valid": not issues, "normalized": normalized, "issues": issues}


async def validate_email(email: str) -> Dict[str, Any]:
    """Validate and normalize an email address."""
    normalized, issues = _validate_email_regex(email)
    return {"valid": not issues, "normalized": normalized, "issues": issues}


async def validate_phone(phone: str) -> Dict[str, Any]:
    """Validate and normalize an international phone number."""
    normalized = _normalize_phone(phone)
    issues = [] if normalized else ["invalid_phone"]
    return {"valid": not issues, "normalized": normalized, "issues": issues}


async def validate_sms(number: str, message: Optional[str] = None) -> Dict[str, Any]:
    """Validate an SMS payload and normalize its contents."""
    phone_result = await validate_phone(number)
    issues = list(phone_result["issues"])

    normalized_message: Optional[str] = None
    if message is not None:
        if not isinstance(message, str):
            issues.append("invalid_message")
        else:
            normalized_message = message.strip()
            if normalized_message and len(normalized_message) > 1000:
                issues.append("message_too_long")

    normalized = f"{phone_result['normalized'] or ''}|{normalized_message or ''}".rstrip("|")
    return {"valid": not issues, "normalized": normalized or None, "issues": issues}


async def validate_whatsapp(number: str, message: Optional[str] = None) -> Dict[str, Any]:
    """Validate a WhatsApp payload and normalize its contents."""
    phone_result = await validate_phone(number)
    issues = list(phone_result["issues"])

    normalized_message: Optional[str] = None
    if message is not None:
        if not isinstance(message, str):
            issues.append("invalid_message")
        else:
            normalized_message = message.strip()
            if normalized_message and len(normalized_message) > 1000:
                issues.append("message_too_long")

    normalized = f"{phone_result['normalized'] or ''}|{normalized_message or ''}".rstrip("|")
    return {"valid": not issues, "normalized": normalized or None, "issues": issues}


async def validate_wifi(ssid: str, password: Optional[str], encryption: str) -> Dict[str, Any]:
    """Validate a Wi-Fi payload and normalize it into a compact string."""
    issues: List[str] = []

    normalized_ssid = ssid.strip() if isinstance(ssid, str) else ""
    if not normalized_ssid:
        issues.append("empty_ssid")

    normalized_encryption = encryption.strip().upper() if isinstance(encryption, str) else ""
    if normalized_encryption not in _VALID_WIFI_ENCRYPTION:
        issues.append("invalid_wifi_encryption")

    normalized_password: Optional[str] = None
    if normalized_encryption != "NOPASS":
        if not isinstance(password, str):
            issues.append("invalid_wifi_password")
        else:
            normalized_password = password.strip()
            if not normalized_password or len(normalized_password) < 8 or len(normalized_password) > 63:
                issues.append("invalid_wifi_password")
    elif isinstance(password, str):
        normalized_password = password.strip() or None

    normalized = f"{normalized_ssid}|{normalized_password or ''}|{normalized_encryption}".rstrip("|")
    return {"valid": not issues, "normalized": normalized or None, "issues": issues}


async def validate_vcard(value: str) -> Dict[str, Any]:
    """Validate a vCard payload by checking the basic structure markers."""
    if not isinstance(value, str):
        return {"valid": False, "normalized": None, "issues": ["invalid_vcard"]}

    trimmed = value.strip()
    issues: List[str] = []
    upper_value = trimmed.upper()
    if "BEGIN:VCARD" not in upper_value or "END:VCARD" not in upper_value:
        issues.append("invalid_vcard")

    if not re.search(r"(?im)^FN:.*$", trimmed):
        issues.append("invalid_vcard")

    return {"valid": not issues, "normalized": trimmed or None, "issues": issues}


async def validate_location(latitude: Any, longitude: Any) -> Dict[str, Any]:
    """Validate latitude and longitude coordinates."""
    try:
        latitude_value = float(latitude)
        longitude_value = float(longitude)
    except (TypeError, ValueError):
        return {"valid": False, "normalized": None, "issues": ["invalid_coordinates"]}

    issues: List[str] = []
    if not -90 <= latitude_value <= 90 or not -180 <= longitude_value <= 180:
        issues.append("invalid_coordinates")

    normalized = f"{latitude_value},{longitude_value}"
    return {"valid": not issues, "normalized": normalized, "issues": issues}


async def validate_social(platform: str, username: str) -> Dict[str, Any]:
    """Validate a social handle for a supported platform."""
    normalized_platform = _normalize_social_platform(platform)
    if not normalized_platform:
        return {"valid": False, "normalized": None, "issues": ["unsupported_platform"]}

    normalized_username = username.strip().lower() if isinstance(username, str) else ""
    issues: List[str] = []
    if not normalized_username:
        issues.append("empty_username")
    else:
        pattern = _SUPPORTED_SOCIAL_PLATFORMS[normalized_platform]
        if not re.fullmatch(pattern, normalized_username):
            issues.append("invalid_social_username")

    normalized = f"{normalized_platform}:{normalized_username}" if normalized_username else None
    return {"valid": not issues, "normalized": normalized, "issues": issues}


async def validate_input(qr_type: str, value: str) -> Dict[str, Any]:
    """Dispatch validation to the appropriate async validator for the QR type."""
    normalized_type = (qr_type or "").strip().lower()

    if normalized_type == "url":
        return await validate_url(value)

    if normalized_type == "text":
        return await validate_text(value)

    if normalized_type == "email":
        return await validate_email(value)

    if normalized_type == "phone":
        return await validate_phone(value)

    if normalized_type == "sms":
        parts = _split_payload(value)
        if len(parts) >= 2:
            return await validate_sms(parts[0], parts[1])
        return await validate_sms(value, "")

    if normalized_type == "whatsapp":
        parts = _split_payload(value)
        if len(parts) >= 2:
            return await validate_whatsapp(parts[0], parts[1])
        return await validate_whatsapp(value, "")

    if normalized_type == "wifi":
        parts = _split_payload(value, "|")
        if len(parts) >= 3:
            return await validate_wifi(parts[0], parts[1], parts[2])
        return await validate_wifi(value, None, "nopass")

    if normalized_type == "vcard":
        return await validate_vcard(value)

    if normalized_type == "location":
        parts = _split_payload(value, ",")
        if len(parts) >= 2:
            return await validate_location(parts[0], parts[1])
        return {"valid": False, "normalized": None, "issues": ["invalid_coordinates"]}

    if normalized_type == "social":
        parts = _split_payload(value, ":")
        if len(parts) >= 2:
            return await validate_social(parts[0], parts[1])
        return {"valid": False, "normalized": None, "issues": ["unsupported_platform"]}

    return {"valid": False, "normalized": None, "issues": ["unsupported_type"]}
