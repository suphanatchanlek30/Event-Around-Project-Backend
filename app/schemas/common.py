# app/schemas/common.py

from typing import Any

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Any | None = None