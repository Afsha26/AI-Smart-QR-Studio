from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


from backend.services.ai_service import generate_theme as svc_generate_theme, generate_content as svc_generate_content

router = APIRouter()


class PromptIn(BaseModel):
    prompt: str
    type: str | None = None

@router.post('/theme')
async def theme(payload: PromptIn):
    """Generate a UI theme suggestion based on the provided prompt.

    This endpoint delegates to `backend.services.ai_service` which should contain
    the actual integration with the AI provider.
    """
    try:
        result = await svc_generate_theme(payload.prompt)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/content')
async def content(payload: PromptIn):
    """Generate marketing copy or QR content suggestions.

    Delegates to service layer.
    """
    try:
        result = await svc_generate_content(payload.prompt, payload.type)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
