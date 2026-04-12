from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.event import SaveEventRequest
from app.services.event_service import EventService

router = APIRouter(prefix="/saved-events", tags=["saved-events"])


@router.post("", status_code=status.HTTP_201_CREATED)
def save_event(
    payload: SaveEventRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.save_event(
        event_id=payload.event_id,
        current_user=current_user,
    )
