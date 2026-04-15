# app/services/auth_service.py

from app.core.exceptions import bad_request, conflict, forbidden, unauthorized
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.domain.auth_manager import AuthManager
from app.domain.organizer import Organizer
from app.domain.student import Student
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterOrganizerRequest,
    RegisterStudentRequest,
    UpdateMeRequest,
)
from sqlalchemy.orm import Session


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)
        self.auth_manager = AuthManager()

    def _to_domain_user(self, user: User) -> Student | Organizer:
        if user.role == "ORGANIZER":
            return Organizer(
                user_id=user.id,
                name=user.full_name,
                email=user.email,
                password_hash=user.password_hash,
            )

        return Student(
            user_id=user.id,
            name=user.full_name,
            email=user.email,
            password_hash=user.password_hash,
        )

    def _validate_password_confirmation(self, password: str, confirm_password: str, field_name: str) -> None:
        if password != confirm_password:
            raise bad_request(
                message="ข้อมูลไม่ถูกต้อง",
                errors=[
                    {
                        "field": field_name,
                        "code": "PASSWORD_MISMATCH",
                        "detail": f"{field_name} ไม่ตรงกับรหัสผ่านที่ระบุ",
                    }
                ],
            )

    def _ensure_email_unique(self, email: str) -> None:
        existing_user = self.user_repo.get_by_email(email)
        domain_users = [self._to_domain_user(existing_user)] if existing_user is not None else []
        self.auth_manager.set_users(domain_users)
        if not self.auth_manager.is_email_unique(email):
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

    def _to_user_data(self, user: User) -> dict:
        return {
            "userId": user.id,
            "fullName": user.full_name,
            "email": user.email,
            "role": user.role,
            "isActive": user.is_active,
            "profileImageUrl": user.profile_image_url,
        }

    def _issue_tokens(self, user: User) -> dict:
        access_token, expires_in = create_access_token(user_id=user.id, role=user.role)
        refresh_token, refresh_expires_at = create_refresh_token(user_id=user.id, role=user.role)
        self.refresh_token_repo.create(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=refresh_expires_at,
        )

        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokenType": "Bearer",
            "expiresIn": expires_in,
        }

    def register_student(self, payload: RegisterStudentRequest):
        self._validate_password_confirmation(payload.password, payload.confirm_password, "confirmPassword")
        self._ensure_email_unique(payload.email)

        password_hash = get_password_hash(payload.password)

        domain_user = self.auth_manager.register_student(
            name=payload.full_name,
            email=payload.email,
            password=password_hash,
        )

        user = self.user_repo.create_user(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=password_hash,
            role=domain_user.get_role(),
        )

        return {
            "success": True,
            "message": "สมัครสมาชิกนักศึกษาสำเร็จ",
            "data": {
                "userId": user.id,
                "fullName": user.full_name,
                "email": user.email,
                "role": domain_user.get_role(),
            },
        }

    def register_organizer(self, payload: RegisterOrganizerRequest):
        self._validate_password_confirmation(payload.password, payload.confirm_password, "confirmPassword")
        self._ensure_email_unique(payload.email)

        password_hash = get_password_hash(payload.password)

        domain_user = self.auth_manager.register_organizer(
            name=payload.full_name,
            email=payload.email,
            password=password_hash,
        )

        user = self.user_repo.create_user(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=password_hash,
            role=domain_user.get_role(),
        )

        return {
            "success": True,
            "message": "สมัครสมาชิกผู้จัดกิจกรรมสำเร็จ",
            "data": {
                "userId": user.id,
                "fullName": user.full_name,
                "email": user.email,
                "role": domain_user.get_role(),
            },
        }

    def login(self, payload: LoginRequest):
        user = self.user_repo.get_by_email(payload.email)
        if user is None:
            raise unauthorized(
                message="อีเมลหรือรหัสผ่านไม่ถูกต้อง",
                errors=[
                    {
                        "field": "email",
                        "code": "INVALID_CREDENTIALS",
                        "detail": "ไม่สามารถเข้าสู่ระบบด้วยข้อมูลนี้ได้",
                    }
                ],
            )

        domain_user = self._to_domain_user(user)
        self.auth_manager.set_users([domain_user])
        try:
            self.auth_manager.login(
                payload.email,
                payload.password,
                password_verifier=lambda _domain_user, plain_password: verify_password(plain_password, user.password_hash),
            )
        except ValueError:
            raise unauthorized(
                message="อีเมลหรือรหัสผ่านไม่ถูกต้อง",
                errors=[
                    {
                        "field": "email",
                        "code": "INVALID_CREDENTIALS",
                        "detail": "ไม่สามารถเข้าสู่ระบบด้วยข้อมูลนี้ได้",
                    }
                ],
            ) from None

        if not user.is_active:
            raise forbidden("บัญชีผู้ใช้งานถูกปิดการใช้งาน")

        tokens = self._issue_tokens(user)
        return {
            "success": True,
            "message": "เข้าสู่ระบบสำเร็จ",
            "data": {
                **tokens,
                "user": {
                    "userId": user.id,
                    "fullName": user.full_name,
                    "email": user.email,
                    "role": user.role,
                },
            },
        }

    def refresh(self, payload: RefreshTokenRequest):
        refresh_token_hash = hash_token(payload.refresh_token)
        token_row = self.refresh_token_repo.get_active_by_hash(refresh_token_hash)
        if token_row is None:
            raise unauthorized("โทเค็นหมดอายุหรือถูกยกเลิกแล้ว")

        decoded = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = decoded.get("sub")
        if user_id is None:
            raise unauthorized("โทเค็นไม่ถูกต้อง")

        user = self.user_repo.get_by_id(int(user_id))
        if user is None or not user.is_active:
            raise forbidden("บัญชีผู้ใช้งานถูกปิดการใช้งาน")

        # rotate refresh token every refresh call
        self.refresh_token_repo.revoke_by_hash(refresh_token_hash)
        tokens = self._issue_tokens(user)

        return {
            "success": True,
            "message": "ต่ออายุโทเค็นสำเร็จ",
            "data": tokens,
        }

    def logout(self, refresh_token: str):
        self.refresh_token_repo.revoke_by_hash(hash_token(refresh_token))
        return {
            "success": True,
            "message": "ออกจากระบบสำเร็จ",
            "data": None,
        }

    def get_me(self, current_user: User):
        return {
            "success": True,
            "message": "ดึงข้อมูลผู้ใช้สำเร็จ",
            "data": self._to_user_data(current_user),
        }

    def update_me(self, current_user: User, payload: UpdateMeRequest):
        if payload.full_name is None and payload.profile_image_url is None:
            raise bad_request(
                message="ข้อมูลไม่ถูกต้อง",
                errors=[
                    {
                        "field": "body",
                        "code": "EMPTY_UPDATE_PAYLOAD",
                        "detail": "ต้องระบุข้อมูลอย่างน้อย 1 ฟิลด์เพื่ออัปเดต",
                    }
                ],
            )

        updated_user = self.user_repo.update_profile(
            user=current_user,
            full_name=payload.full_name,
            profile_image_url=payload.profile_image_url,
        )
        return {
            "success": True,
            "message": "อัปเดตข้อมูลผู้ใช้สำเร็จ",
            "data": self._to_user_data(updated_user),
        }

    def change_password(self, current_user: User, payload: ChangePasswordRequest):
        if not verify_password(payload.old_password, current_user.password_hash):
            raise unauthorized(
                message="รหัสผ่านเดิมไม่ถูกต้อง",
                errors=[
                    {
                        "field": "oldPassword",
                        "code": "OLD_PASSWORD_INCORRECT",
                        "detail": "ไม่สามารถยืนยันรหัสผ่านเดิมได้",
                    }
                ],
            )

        self._validate_password_confirmation(
            payload.new_password,
            payload.confirm_new_password,
            "confirmNewPassword",
        )

        if payload.old_password == payload.new_password:
            raise bad_request(
                message="ข้อมูลไม่ถูกต้อง",
                errors=[
                    {
                        "field": "newPassword",
                        "code": "PASSWORD_NOT_CHANGED",
                        "detail": "รหัสผ่านใหม่ต้องไม่ซ้ำกับรหัสผ่านเดิม",
                    }
                ],
            )

        new_hash = get_password_hash(payload.new_password)
        self.user_repo.update_password(current_user, new_hash)
        self.refresh_token_repo.revoke_all_for_user(current_user.id)

        return {
            "success": True,
            "message": "เปลี่ยนรหัสผ่านสำเร็จ",
            "data": None,
        }