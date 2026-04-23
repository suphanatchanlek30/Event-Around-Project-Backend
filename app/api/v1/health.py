# app/api/v1/health.py

from datetime import UTC, datetime

from app.core.settings import settings
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
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