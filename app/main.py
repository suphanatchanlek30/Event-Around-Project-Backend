# app/main.py

from datetime import UTC, datetime

from app.api.v1.api import api_router
from app.core.settings import settings
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


def build_standard_health_response() -> dict:
    return {
        "success": True,
        "message": "Event Around API is running",
        "data": {
            "service": settings.app_name,
            "environment": settings.app_env,
            "apiPrefix": settings.api_v1_prefix,
            "serverTime": datetime.now(UTC).isoformat(),
        },
    }

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "errors": [],
        },
    )


@app.get("/")
def root():
    return {
        "success": True,
        "message": "Welcome to Event Around API",
        "data": {
            "service": settings.app_name,
            "environment": settings.app_env,
            "apiPrefix": settings.api_v1_prefix,
        },
    }


@app.get("/health", tags=["health"])
def root_health_check():
    return build_standard_health_response()


app.include_router(api_router, prefix=settings.api_v1_prefix)