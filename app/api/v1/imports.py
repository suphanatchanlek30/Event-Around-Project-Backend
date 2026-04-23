from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.event import EventImportRequest
from app.services.event_service import EventService
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/import", tags=["import"])


@router.get("/history", status_code=status.HTTP_200_OK)
def get_import_history(
    page: int | None = Query(default=1, ge=1),
    page_size: int | None = Query(default=10, alias="pageSize", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.get_import_history(
        page=page,
        page_size=page_size,
        current_user=current_user,
    )


@router.post("/events/csv", status_code=status.HTTP_200_OK)
def import_events_csv(
    file: UploadFile = File(...),
    default_status: str | None = Form(default="DRAFT", alias="defaultStatus"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.import_events_from_csv(
        file=file,
        default_status=default_status,
        current_user=current_user,
    )


@router.post("/events/json", status_code=status.HTTP_200_OK)
def import_events_json(
    payload: EventImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(db)
    return service.import_events_from_json(
        payload=payload,
        current_user=current_user,
    )
