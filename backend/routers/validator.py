from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from backend.services.validator_service import validate_url as svc_validate_url

router = APIRouter()


class ValidationRequest(BaseModel):
    type: str
    value: str


@router.post('/')
async def validator(payload: ValidationRequest):
    """Validate and sanitize a URL using backend rules.

    Business rules live in `backend.services.validator_service`.
    """
    try:
        if payload.type == "url":
            result = await svc_validate_url(payload.value)
            return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
