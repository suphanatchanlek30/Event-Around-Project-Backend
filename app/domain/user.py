from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.security import verify_password


class User(ABC):
    def __init__(self, user_id: int, name: str, email: str, password_hash: str):
        self._user_id = user_id
        self._name = name.strip()
        self._email = email.lower().strip()
        self._password_hash = password_hash

    def get_user_id(self) -> int:
        return self._user_id

    def get_name(self) -> str:
        return self._name

    def set_name(self, name: str) -> None:
        self._name = name.strip()

    def get_email(self) -> str:
        return self._email

    def set_email(self, email: str) -> None:
        self._email = email.lower().strip()

    def verify_password(self, password: str) -> bool:
        return verify_password(password, self._password_hash)

    @abstractmethod
    def get_role(self) -> str:
        raise NotImplementedError
