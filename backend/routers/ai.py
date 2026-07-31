import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.gemini_service import (
    GeminiConfigurationError,
    GeminiService,
    GeminiServiceError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


class AIResponse(BaseModel):
    """Standard response envelope for AI endpoints."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class GenerateRequest(BaseModel):
    """Request payload for QR generation."""

    prompt: str = Field(min_length=1)


class ThemeRequest(BaseModel):
    """Request payload for theme suggestions."""

    prompt: str = Field(min_length=1)


class ImproveRequest(BaseModel):
    """Request payload for QR improvement suggestions."""

    payload: str = Field(min_length=1)
    style: dict[str, Any] = Field(default_factory=dict)


class ExplainRequest(BaseModel):
    """Request payload for QR explanations."""

    payload: str = Field(min_length=1)


def _build_success_response(data: dict[str, Any] | None = None) -> AIResponse:
    return AIResponse(success=True, data=data, error=None)


def _build_error_response(message: str) -> AIResponse:
    return AIResponse(success=False, data=None, error=message)


def _get_gemini_service() -> GeminiService:
    try:
        return GeminiService()
    except GeminiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/generate", response_model=AIResponse)
async def generate(payload: GenerateRequest) -> AIResponse:
    """Convert a natural-language request into a QR configuration."""
    logger.info("AI generate endpoint called")
    try:
        service = _get_gemini_service()
        data = await service.generate_qr_configuration(payload.prompt)
        logger.info("AI generate endpoint completed")
        return _build_success_response(data)
    except HTTPException:
        raise
    except GeminiServiceError as exc:
        logger.exception("Gemini generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while generating QR configuration")
        raise HTTPException(status_code=500, detail="Unexpected server error") from exc


@router.post("/theme", response_model=AIResponse)
async def theme(payload: ThemeRequest) -> AIResponse:
    """Suggest a visual theme for a QR code."""
    logger.info("AI theme endpoint called")
    try:
        service = _get_gemini_service()
        data = await service.suggest_theme(payload.prompt)
        logger.info("AI theme endpoint completed")
        return _build_success_response(data)
    except HTTPException:
        raise
    except GeminiServiceError as exc:
        logger.exception("Gemini theme generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while generating theme")
        raise HTTPException(status_code=500, detail="Unexpected server error") from exc


@router.post("/improve", response_model=AIResponse)
async def improve(payload: ImproveRequest) -> AIResponse:
    """Recommend QR improvements based on an existing configuration."""
    logger.info("AI improve endpoint called")
    try:
        service = _get_gemini_service()
        data = await service.improve_qr({"payload": payload.payload, "style": payload.style})
        logger.info("AI improve endpoint completed")
        return _build_success_response(data)
    except HTTPException:
        raise
    except GeminiServiceError as exc:
        logger.exception("Gemini improvement generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while improving QR")
        raise HTTPException(status_code=500, detail="Unexpected server error") from exc


@router.post("/explain", response_model=AIResponse)
async def explain(payload: ExplainRequest) -> AIResponse:
    """Explain what a QR code does in simple language."""
    logger.info("AI explain endpoint called")
    try:
        service = _get_gemini_service()
        data = await service.explain_qr(payload.payload)
        logger.info("AI explain endpoint completed")
        return _build_success_response(data)
    except HTTPException:
        raise
    except GeminiServiceError as exc:
        logger.exception("Gemini explanation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while explaining QR")
        raise HTTPException(status_code=500, detail="Unexpected server error") from exc
