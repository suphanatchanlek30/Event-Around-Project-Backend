from app.core.database import get_db
from app.core.security import get_current_user
from app.core.timezone import serialize_datetime_payload
from app.models.user import User
from app.schemas.category import CategoryCreateRequest, CategoryUpdateRequest
from app.services.category_service import CategoryService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", status_code=status.HTTP_200_OK)
def list_categories(
    include_inactive: str | None = Query(default=None, alias="includeInactive"),
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    return serialize_datetime_payload(service.list_categories(include_inactive))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    return serialize_datetime_payload(service.create_category(payload, current_user))


@router.get("/{categoryId}", status_code=status.HTTP_200_OK)
def get_category_detail(categoryId: int, db: Session = Depends(get_db)):
    service = CategoryService(db)
    return serialize_datetime_payload(service.get_category_detail(categoryId))


@router.patch("/{categoryId}", status_code=status.HTTP_200_OK)
def update_category(
    categoryId: int,
    payload: CategoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    return serialize_datetime_payload(service.update_category(categoryId, payload, current_user))


@router.delete("/{categoryId}", status_code=status.HTTP_200_OK)
def deactivate_category(
    categoryId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    return serialize_datetime_payload(service.deactivate_category(categoryId, current_user))
