"""Production-ready Gemini service for AI Smart QR Studio.

This module is the single backend integration point for Gemini. It uses the
official google-genai SDK, reusable prompt templates, and structured JSON
parsing so the rest of the backend can stay focused on QR workflows.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv

try:
    from google import genai
except ModuleNotFoundError:  # pragma: no cover - optional dependency handling
    genai = None  # type: ignore[assignment]

try:
    from google.genai import types as genai_types
except ModuleNotFoundError:  # pragma: no cover - optional dependency handling
    genai_types = None  # type: ignore[assignment]

from backend.prompts.qr_prompt import (
    EXPLAIN_PROMPT,
    SYSTEM_PROMPT,
    build_explain_prompt,
    build_generate_qr_prompt,
    build_improve_prompt,
    build_theme_prompt,
)

logger = logging.getLogger(__name__)

_service_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_service_dir)
_project_root = os.path.dirname(_backend_dir)
load_dotenv(dotenv_path=os.path.join(_backend_dir, ".env"))
load_dotenv(dotenv_path=os.path.join(_project_root, ".env"))

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
DEFAULT_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.4"))
MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "1024"))
REQUEST_TIMEOUT = float(os.getenv("GEMINI_REQUEST_TIMEOUT", "60"))

_API_KEY_PATTERN = re.compile(r"(?i)(AIza[0-9A-Za-z_-]{20,})")
_KEY_VALUE_PATTERN = re.compile(
    r"(?i)(['\"]?(?:api[_ -]?key|key|token)['\"]?\s*[:=]\s*['\"]?)([^,\s'\"&}]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/-]+=*")
_AUTHORIZATION_PATTERN = re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+")


def _http_status_code(exc: Exception) -> int | None:
    candidates = (
        getattr(exc, "status_code", None),
        getattr(getattr(exc, "response", None), "status_code", None),
        getattr(exc, "code", None),
    )
    for candidate in candidates:
        try:
            status = int(candidate)
        except (TypeError, ValueError):
            continue
        if 100 <= status <= 599:
            return status
    return None


def _sanitized_error_detail(exc: Exception) -> str:
    detail = " ".join(str(exc).split())
    detail = _API_KEY_PATTERN.sub("[REDACTED]", detail)
    detail = _KEY_VALUE_PATTERN.sub(r"\1[REDACTED]", detail)
    detail = _BEARER_PATTERN.sub(r"\1[REDACTED]", detail)
    detail = _AUTHORIZATION_PATTERN.sub(r"\1[REDACTED]", detail)
    return detail[:500]


class GeminiServiceError(Exception):
    """Base exception for Gemini service failures."""


class GeminiConfigurationError(GeminiServiceError):
    """Raised when the Gemini configuration is missing or invalid."""


class GeminiAuthenticationError(GeminiConfigurationError):
    """Raised when the Gemini API key is rejected."""


class GeminiQuotaError(GeminiServiceError):
    """Raised when the Gemini API quota has been exhausted."""


class GeminiTimeoutError(GeminiServiceError):
    """Raised when a Gemini request times out."""


class GeminiResponseError(GeminiServiceError):
    """Raised when Gemini returns malformed or empty content."""


class GeminiService:
    """Thin service wrapper around the official Gemini SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        request_timeout: Optional[float] = None,
    ) -> None:
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._model = model or DEFAULT_MODEL
        self._temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE
        self._max_output_tokens = max_output_tokens or MAX_OUTPUT_TOKENS
        self._request_timeout = request_timeout if request_timeout is not None else REQUEST_TIMEOUT
        self._client: Any | None = None

        self._validate_configuration()
        self._initialize_client()

    def _validate_configuration(self) -> None:
        if not self._api_key:
            raise GeminiConfigurationError("GEMINI_API_KEY is missing. Set it in the environment or .env file.")

    def _initialize_client(self) -> None:
        if genai is None:
            logger.warning(
                "The google-genai SDK is not installed; requests will fail until it is installed."
            )
            self._client = None
            return

        self._client = genai.Client(api_key=self._api_key)

    @property
    def client(self) -> Any:
        if self._client is None:
            self._initialize_client()
        return self._client

    async def generate_qr_configuration(self, user_prompt: str) -> Dict[str, Any]:
        """Create a structured QR configuration from a natural-language prompt."""
        prompt = build_generate_qr_prompt(user_prompt)
        return await self._generate_json_response(prompt, operation_name="generate_qr_configuration")

    async def suggest_theme(self, user_prompt: str) -> Dict[str, Any]:
        """Suggest a visual theme without generating QR payload content."""
        prompt = build_theme_prompt(user_prompt)
        return await self._generate_json_response(prompt, operation_name="suggest_theme")

    async def improve_qr(self, existing_configuration: Dict[str, Any] | str) -> Dict[str, Any]:
        """Recommend QR improvements for an existing configuration."""
        if isinstance(existing_configuration, dict):
            payload = json.dumps(existing_configuration, indent=2)
        else:
            payload = existing_configuration
        prompt = build_improve_prompt(payload)
        return await self._generate_json_response(prompt, operation_name="improve_qr")

    async def explain_qr(self, payload: str) -> Dict[str, Any]:
        """Explain the purpose of a QR code in structured JSON."""
        prompt = build_explain_prompt(payload)
        return await self._generate_json_response(prompt, operation_name="explain_qr")

    async def _generate_json_response(self, prompt: str, operation_name: str) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            raise GeminiResponseError("The Gemini prompt cannot be empty.")

        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
        logger.info("Gemini request started for %s using model %s", operation_name, self._model)
        started_at = time.perf_counter()

        try:
            response = await asyncio.wait_for(
                self._send_request(full_prompt),
                timeout=self._request_timeout,
            )
        except asyncio.TimeoutError as exc:
            logger.error(
                "Gemini provider failure operation=%s exception_class=%s "
                "http_status=none provider_code=none detail=%s",
                operation_name,
                type(exc).__name__,
                _sanitized_error_detail(exc),
            )
            raise GeminiTimeoutError("Gemini request timed out.") from exc
        except Exception as exc:  # pragma: no cover - exercised via runtime errors
            self._log_api_error(exc, operation_name)
            raise self._wrap_api_error(exc) from exc

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "Gemini response received for %s in %.2f ms using model %s",
            operation_name,
            elapsed_ms,
            self._model,
        )

        text = self._extract_response_text(response)
        if not text or not text.strip():
            raise GeminiResponseError("Gemini returned an empty response.")

        cleaned_text = self._strip_markdown_code_fences(text)
        return self._parse_json_response(cleaned_text, operation_name)

    async def _send_request(self, prompt: str) -> Any:
        if self._client is None:
            raise GeminiConfigurationError(
                "The google-genai SDK is not available. Install it with 'pip install google-genai'."
            )

        config = self._build_generation_config()
        request_kwargs: Dict[str, Any] = {
            "model": self._model,
            "contents": prompt,
        }
        if config is not None:
            request_kwargs["config"] = config

        async_client = getattr(self._client, "aio", None)
        async_models = getattr(async_client, "models", None) if async_client is not None else None
        async_generate_content = getattr(async_models, "generate_content", None)
        if callable(async_generate_content) and inspect.iscoroutinefunction(async_generate_content):
            return await async_generate_content(**request_kwargs)

        return await asyncio.to_thread(
            self.client.models.generate_content,
            **request_kwargs,
        )

    def _build_generation_config(self) -> Any:
        if genai_types is None:
            return None

        supported_kwargs: Dict[str, Any] = {}
        try:
            signature = inspect.signature(genai_types.GenerateContentConfig)
        except (TypeError, ValueError):
            signature = None

        if signature is not None:
            if "temperature" in signature.parameters:
                supported_kwargs["temperature"] = self._temperature
            if "max_output_tokens" in signature.parameters:
                supported_kwargs["max_output_tokens"] = self._max_output_tokens
            if "response_mime_type" in signature.parameters:
                supported_kwargs["response_mime_type"] = "application/json"
            if "timeout" in signature.parameters:
                supported_kwargs["timeout"] = self._request_timeout
        else:
            supported_kwargs = {
                "temperature": self._temperature,
                "max_output_tokens": self._max_output_tokens,
                "response_mime_type": "application/json",
            }

        if not supported_kwargs:
            return None

        return genai_types.GenerateContentConfig(**supported_kwargs)

    def _extract_response_text(self, response: Any) -> str:
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text

        if hasattr(response, "candidates"):
            for candidate in response.candidates:
                content = getattr(candidate, "content", None)
                parts = getattr(content, "parts", None) or []
                for part in parts:
                    part_text = getattr(part, "text", None)
                    if isinstance(part_text, str) and part_text.strip():
                        return part_text

        return ""

    def _strip_markdown_code_fences(self, text: str) -> str:
        cleaned_text = text.strip()
        match = re.search(r"```(?:json|jsonc|javascript|python)?\s*(.*?)\s*```", cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(1).strip()
        return cleaned_text

    def _parse_json_response(self, content: str, operation_name: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise GeminiResponseError(
                f"Gemini returned invalid JSON for {operation_name}."
            ) from exc

        if not isinstance(parsed, dict):
            raise GeminiResponseError(f"Gemini response for {operation_name} was not a JSON object.")

        return parsed

    def _wrap_api_error(self, exc: Exception) -> GeminiServiceError:
        message = str(exc).lower()
        status = _http_status_code(exc)
        if status in (401, 403) or any(
            phrase in message for phrase in ("api key", "unauthorized", "authentication")
        ):
            return GeminiAuthenticationError("Gemini authentication failed. Verify GEMINI_API_KEY.")
        if status == 429 or any(phrase in message for phrase in ("quota", "429", "rate limit")):
            return GeminiQuotaError("Gemini quota exceeded. Check your account limits or try again later.")
        if (
            "timeout" in type(exc).__name__.lower()
            or "deadline" in type(exc).__name__.lower()
            or any(phrase in message for phrase in ("timeout", "timed out", "deadline"))
        ):
            return GeminiTimeoutError("Gemini request timed out. Please try again.")
        if status == 404 and any(phrase in message for phrase in ("model", "not_found", "not found")):
            return GeminiModelError("The configured Gemini model is unavailable.")
        if status == 503 or "service unavailable" in message:
            return GeminiUnavailableError("Gemini service is temporarily unavailable.")
        return GeminiAPIError("Gemini request failed. Check the backend logs for details.")

    def _log_api_error(self, exc: Exception, operation_name: str) -> None:
        raw_code = getattr(exc, "code", None)
        provider_code = raw_code if raw_code is not None and _http_status_code(exc) != raw_code else None
        logger.error(
            "Gemini provider failure operation=%s exception_class=%s http_status=%s "
            "provider_code=%s detail=%s",
            operation_name,
            type(exc).__name__,
            _http_status_code(exc) or "none",
            provider_code if provider_code is not None else "none",
            _sanitized_error_detail(exc),
        )


class GeminiAPIError(GeminiServiceError):
    """Raised when the Gemini API returns a generic failure."""


class GeminiModelError(GeminiAPIError):
    """Raised when the configured Gemini model is not available."""


class GeminiUnavailableError(GeminiAPIError):
    """Raised when the Gemini service is temporarily unavailable."""


async def generate_text(prompt: str, max_tokens: int = 256) -> Dict[str, Any]:
    """Compatibility wrapper that returns a simple text payload dictionary."""
    if not prompt or not prompt.strip():
        raise ValueError("prompt is required")

    service = GeminiService(api_key=os.getenv("GEMINI_API_KEY"))
    response = await service._generate_json_response(prompt, operation_name="generate_text")
    return {
        "text": json.dumps(response),
        "meta": {"source": "gemini_service"},
    }


__all__ = [
    "GeminiAPIError",
    "GeminiAuthenticationError",
    "GeminiConfigurationError",
    "GeminiModelError",
    "GeminiQuotaError",
    "GeminiResponseError",
    "GeminiService",
    "GeminiServiceError",
    "GeminiTimeoutError",
    "GeminiUnavailableError",
    "generate_text",
]
