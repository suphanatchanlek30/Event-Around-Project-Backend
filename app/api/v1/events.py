from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_current_user
from app.models.user import User
from app.schemas.event import (
    EventCancelRequest,
    EventCreateRequest,
    EventUpdateRequest,
)
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", status_code=status.HTTP_200_OK)
def list_events(
    page: int | None = Query(default=1, ge=1),
    page_size: int | None = Query(default=10, alias="pageSize", ge=1, le=100),
    search: str | None = Query(default=None),
    category_id: int | None = Query(default=None, alias="categoryId", ge=1),
    status: str | None = Query(default=None),
    start_from: str | None = Query(default=None, alias="startFrom"),
    end_to: str | None = Query(default=None, alias="endTo"),
    sort_by: str | None = Query(default=None, alias="sortBy"),
    sort_order: str | None = Query(default=None, alias="sortOrder"),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    return service.list_events(
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        status=status,
        start_from=start_from,
        end_to=end_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.create_event(payload, current_user)


@router.patch("/{event_id}", status_code=status.HTTP_200_OK)
def update_event(
    event_id: int,
    payload: EventUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.update_event(event_id=event_id, payload=payload, current_user=current_user)


@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.delete_event(event_id=event_id, current_user=current_user)


@router.post("/{event_id}/publish", status_code=status.HTTP_200_OK)
def publish_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.publish_event(event_id=event_id, current_user=current_user)


@router.post("/{event_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_event(
    event_id: int,
    payload: EventCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.cancel_event(event_id=event_id, payload=payload, current_user=current_user)


@router.get("/{event_id}", status_code=status.HTTP_200_OK)
def get_event_detail(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    service = EventService(db)
    return service.get_event_detail(event_id=event_id, current_user=current_user)
