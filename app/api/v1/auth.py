# app/api/v1/auth.py

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.timezone import serialize_datetime_payload
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshTokenRequest,
    RegisterOrganizerRequest,
    RegisterStudentRequest,
    UpdateMeRequest,
)
from app.services.auth_service import AuthService
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/student", status_code=status.HTTP_201_CREATED)
def register_student(payload: RegisterStudentRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return serialize_datetime_payload(service.register_student(payload))


@router.post("/register/organizer", status_code=status.HTTP_201_CREATED)
def register_organizer(payload: RegisterOrganizerRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return serialize_datetime_payload(service.register_organizer(payload))


@router.post("/login", status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return serialize_datetime_payload(service.login(payload))


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return serialize_datetime_payload(service.refresh(payload))


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AuthService(db)
    return serialize_datetime_payload(service.logout(payload.refresh_token))


@router.get("/me", status_code=status.HTTP_200_OK, response_model=MeResponse)
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AuthService(db)
    return serialize_datetime_payload(service.get_me(current_user))


@router.patch("/me", status_code=status.HTTP_200_OK, response_model=MeResponse)
def update_me(
    payload: UpdateMeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AuthService(db)
    return serialize_datetime_payload(service.update_me(current_user, payload))


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AuthService(db)
    return serialize_datetime_payload(service.change_password(current_user, payload))