# app/api/v1/api.py

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.events import router as events_router
from app.api.v1.health import router as health_router
from app.api.v1.imports import router as imports_router
from app.api.v1.organizer import router as organizer_router
from app.api.v1.savedEvent import router as saved_event_router
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(events_router)
api_router.include_router(saved_event_router)
api_router.include_router(organizer_router)
api_router.include_router(imports_router)