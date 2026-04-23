# app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator


class RegisterStudentRequest(BaseModel):
    full_name: str = Field(..., alias="fullName", min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)
    confirm_password: str = Field(..., alias="confirmPassword", min_length=8, max_length=255)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("fullName is required")
        return value

    model_config = {
        "populate_by_name": True
    }


class RegisterOrganizerRequest(RegisterStudentRequest):
    pass


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., alias="refreshToken", min_length=10)

    model_config = {
        "populate_by_name": True
    }


class LogoutRequest(RefreshTokenRequest):
    pass


class UpdateMeRequest(BaseModel):
    full_name: str | None = Field(default=None, alias="fullName", min_length=1, max_length=255)
    profile_image_url: HttpUrl | None = Field(default=None, alias="profileImageUrl")

    @field_validator("full_name")
    @classmethod
    def validate_full_name_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("fullName is required")
        return value

    model_config = {
        "populate_by_name": True
    }


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., alias="oldPassword", min_length=8, max_length=255)
    new_password: str = Field(..., alias="newPassword", min_length=8, max_length=255)
    confirm_new_password: str = Field(..., alias="confirmNewPassword", min_length=8, max_length=255)

    model_config = {
        "populate_by_name": True
    }


class StudentResponseData(BaseModel):
    user_id: int = Field(..., alias="userId")
    full_name: str = Field(..., alias="fullName")
    email: EmailStr
    role: str

    model_config = {
        "populate_by_name": True
    }


class MeResponseData(BaseModel):
    user_id: int = Field(..., alias="userId")
    full_name: str = Field(..., alias="fullName")
    email: EmailStr
    role: str
    is_active: bool = Field(..., alias="isActive")
    profile_image_url: str | None = Field(default=None, alias="profileImageUrl")

    model_config = {
        "populate_by_name": True
    }


class MeResponse(BaseModel):
    success: bool
    message: str
    data: MeResponseData

    model_config = {
        "populate_by_name": True
    }