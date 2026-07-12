from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.validator_service import validate_input

router = APIRouter()


class ValidationRequest(BaseModel):
    type: str
    value: str


@router.post("/")
async def validator(payload: ValidationRequest):
    """
    Validate user input based on the selected QR type.

    All validation logic is handled by
    backend.services.validator_service.
    """
    try:
        result = await validate_input(
            payload.type,
            payload.value
        )
        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )