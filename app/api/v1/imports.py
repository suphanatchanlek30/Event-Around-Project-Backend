from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.event_service import EventService

router = APIRouter(prefix="/import", tags=["import"])


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
