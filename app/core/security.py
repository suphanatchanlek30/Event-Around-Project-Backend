# app/core/security.py

from datetime import datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import forbidden, unauthorized
from app.core.timezone import get_now_utc
from app.repositories.user_repository import UserRepository
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    expires_in = settings.access_token_expire_minutes * 60
    exp = get_now_utc() + timedelta(seconds=expires_in)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": exp,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


def create_refresh_token(user_id: int, role: str) -> tuple[str, datetime]:
    exp_dt = get_now_utc() + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "refresh",
        "jti": str(uuid4()),
        "exp": exp_dt,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, exp_dt


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise unauthorized("โทเค็นไม่ถูกต้อง") from exc

    token_type = payload.get("type")
    if token_type != expected_type:
        raise unauthorized("ประเภทโทเค็นไม่ถูกต้อง")

    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise unauthorized("ไม่ได้รับสิทธิ์การเข้าถึง")

    payload = decode_token(credentials.credentials, expected_type="access")
    user_id = payload.get("sub")
    if user_id is None:
        raise unauthorized("โทเค็นไม่ถูกต้อง")

    user = UserRepository(db).get_by_id(int(user_id))
    if user is None:
        raise unauthorized("ไม่พบผู้ใช้งาน")

    if not user.is_active:
        raise forbidden("บัญชีผู้ใช้งานถูกปิดการใช้งาน")

    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        return None

    payload = decode_token(credentials.credentials, expected_type="access")
    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = UserRepository(db).get_by_id(int(user_id))
    if user is None or not user.is_active:
        return None

    return user