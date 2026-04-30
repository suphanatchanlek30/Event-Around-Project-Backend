from app.core.settings import settings
from app.core.timezone import format_datetime_for_api, get_now_utc
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
            "serverTime": format_datetime_for_api(get_now_utc()),
        },
    }