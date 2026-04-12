from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.event import SaveEventRequest
from app.services.event_service import EventService

router = APIRouter(prefix="/saved-events", tags=["saved-events"])


@router.get("")
def get_saved_events(
    page: int | None = Query(default=None),
    page_size: int | None = Query(default=None, alias="pageSize"),
    status: str | None = Query(default=None),
    sort_by: str | None = Query(default=None, alias="sortBy"),
    sort_order: str | None = Query(default=None, alias="sortOrder"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.get_saved_events(
        page=page,
        page_size=page_size,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
    )


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


@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
def unsave_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.unsave_event(
        event_id=event_id,
        current_user=current_user,
    )
