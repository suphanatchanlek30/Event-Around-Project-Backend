from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.organizer_service import OrganizerService

router = APIRouter(prefix="/organizer", tags=["organizer"])


@router.get("/dashboard", status_code=status.HTTP_200_OK)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = OrganizerService(db)
    return service.get_dashboard(current_user)