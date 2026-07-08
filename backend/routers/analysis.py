from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.analysis_service import analyze_quality as svc_analyze_quality

router = APIRouter()


class AnalyzeIn(BaseModel):
    payload: str
    options: dict | None = None


@router.post('/quality')
async def quality(payload: AnalyzeIn):
    """Analyze QR payload and design options for scan quality.

    Delegates to `backend.services.analysis_service`.
    """
    try:
        result = await svc_analyze_quality(payload.payload, payload.options or {})
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
