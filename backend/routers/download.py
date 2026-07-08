from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from backend.services.download_service import render_download as svc_render_download

router = APIRouter()


class DownloadIn(BaseModel):
    payload: str
    format: str = 'png'
    options: dict | None = None


@router.post('/')
async def download(req: DownloadIn):
    """Render a QR in the requested format and stream it back as a file.

    The heavy lifting is performed by `backend.services.download_service`.
    """
    fmt = req.format.lower()
    try:
        content, mime = await svc_render_download(req.payload, fmt, req.options or {})
        # content should be bytes-like
        return StreamingResponse(iter([content]), media_type=mime, headers={
            'Content-Disposition': f'attachment; filename="qr.{fmt}"'
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
