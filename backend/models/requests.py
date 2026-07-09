from pydantic import BaseModel, EmailStr, Field


class AIThemeRequest(BaseModel):
    prompt: str = Field(..., min_length=10, description='Prompt for AI theme suggestion')


class AIContentRequest(BaseModel):
    prompt: str = Field(..., min_length=10, description='Prompt for AI generated content')


class URLValidatorRequest(BaseModel):
    url: str = Field(..., description='URL to validate')


class QRDownloadRequest(BaseModel):
    data: str = Field(..., description='QR payload data')
    type: str = Field(default='png', description='Download format (png or svg)')
