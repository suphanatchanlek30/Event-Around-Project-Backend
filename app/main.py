# app/main.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
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
        "data": None,
    }


app.include_router(api_router, prefix=settings.api_v1_prefix)