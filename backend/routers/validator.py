from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from backend.services.validator_service import validate_url as svc_validate_url

router = APIRouter()


class URLIn(BaseModel):
    url: str


@router.post('/url')
async def url_validator(payload: URLIn):
    """Validate and sanitize a URL using backend rules.

    Business rules live in `backend.services.validator_service`.
    """
    try:
        result = await svc_validate_url(payload.url)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
