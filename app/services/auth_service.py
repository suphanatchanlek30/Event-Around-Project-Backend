# app/services/auth_service.py

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, conflict
from app.core.security import get_password_hash
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterStudentRequest


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register_student(self, payload: RegisterStudentRequest):
        if payload.password != payload.confirm_password:
            raise bad_request(
                message="ข้อมูลไม่ถูกต้อง",
                errors=[
                    {
                        "field": "confirmPassword",
                        "code": "PASSWORD_MISMATCH",
                        "detail": "password และ confirmPassword ต้องตรงกัน",
                    }
                ],
            )

        existing_user = self.user_repo.get_by_email(payload.email)
        if existing_user:
            raise conflict(
                message="อีเมลนี้ถูกใช้งานแล้ว",
                errors=[
                    {
                        "field": "email",
                        "code": "EMAIL_ALREADY_EXISTS",
                        "detail": "ไม่สามารถใช้อีเมลนี้สมัครสมาชิกได้",
                    }
                ],
            )

        password_hash = get_password_hash(payload.password)

        user = self.user_repo.create_student(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=password_hash,
        )

        return {
            "success": True,
            "message": "สมัครสมาชิกนักศึกษาสำเร็จ",
            "data": {
                "userId": user.id,
                "fullName": user.full_name,
                "email": user.email,
                "role": user.role,
            },
        }