"""FastAPI application entrypoint.

- Enables CORS using environment configuration
- Registers routers (business logic lives in `backend.routers` and `backend.services`)
- Loads environment variables via python-dotenv
- Adds global error handlers for validation and unexpected errors

Note: Keep business logic out of this module. Implement features in `backend.services`.
"""
import os
import logging
from typing import List

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from dotenv import load_dotenv

# Load .env into environment early
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger('aiqr.backend')


def create_app() -> FastAPI:
    app = FastAPI(title='AI Smart QR — API', version='0.1')
    @app.get("/")
    async def home():
        return {
            "message": "AI Smart QR Backend Running"
        }
    # Configure CORS
    origins_env = os.getenv('BACKEND_ALLOWED_ORIGINS', '')
    if origins_env:
        origins = [o.strip() for o in origins_env.split(',') if o.strip()]
    else:
        # sensible defaults for local development
        origins = [
            'http://localhost',
            'http://localhost:3000',
            'http://localhost:5500',
            'http://127.0.0.1',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5500',
            'http://127.0.0.2:5500',
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    # Register routers
    # Routers are thin and delegate to services in backend.services
    from backend.routers import ai, validator, analysis, download

    app.include_router(ai.router, prefix='/ai', tags=['ai'])
    app.include_router(validator.router, prefix='/validator', tags=['validator'])
    app.include_router(analysis.router, prefix='/analysis', tags=['analysis'])
    app.include_router(download.router, prefix='/download', tags=['download'])

    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning('Validation error: %s %s', request.url, exc)
        return JSONResponse(status_code=422, content={
            'detail': exc.errors(),
            'body': exc.body,
        })

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception('Unhandled exception while processing request: %s %s', request.method, request.url)
        return JSONResponse(status_code=500, content={'detail': 'Internal server error'})

    return app


app = create_app()

if __name__ == '__main__':
    # Allow running with `python backend/main.py` for quick development
    import uvicorn
    uvicorn.run('backend.main:app', host='0.0.0.0', port=int(os.getenv('PORT', 8000)), reload=True)
