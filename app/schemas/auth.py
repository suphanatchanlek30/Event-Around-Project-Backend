# app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field, field_validator


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


class StudentResponseData(BaseModel):
    user_id: int = Field(..., alias="userId")
    full_name: str = Field(..., alias="fullName")
    email: EmailStr
    role: str

    model_config = {
        "populate_by_name": True
    }