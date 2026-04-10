# app/api/v1/health.py

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    return {
        "success": True,
        "message": "Event Around API is running",
        "data": None,
    }