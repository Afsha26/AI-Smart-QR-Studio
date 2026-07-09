from pydantic import BaseModel


class AIThemeResponse(BaseModel):
    primary_color: str
    secondary_color: str
    background_color: str
    eye_style: str
    dot_style: str
    title: str
    cta: str
    tagline: str


class AIContentResponse(BaseModel):
    content: str


class ValidationResponse(BaseModel):
    valid: bool
    errors: list[str] = []


class QualityResponse(BaseModel):
    contrast: str
    size: str
    logo: str
    score: int
