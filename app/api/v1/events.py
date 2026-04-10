from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
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
