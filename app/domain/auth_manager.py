from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Callable

from app.domain.organizer import Organizer
from app.domain.student import Student
from app.domain.user import User


class AuthManager:
    def __init__(self):
        self._users: list[User] = []

    def set_users(self, users: Iterable[User]) -> None:
        self._users = list(users)

    def register_student(self, name: str, email: str, password: str) -> Student:
        if not self.is_email_unique(email):
            raise ValueError("EMAIL_ALREADY_EXISTS")

        return Student(
            user_id=0,
            name=name,
            email=email,
            password_hash=password,
        )

    def register_organizer(self, name: str, email: str, password: str) -> Organizer:
        if not self.is_email_unique(email):
            raise ValueError("EMAIL_ALREADY_EXISTS")

        return Organizer(
            user_id=0,
            name=name,
            email=email,
            password_hash=password,
        )

    def login(self, email: str, password: str, password_verifier: Callable[[User, str], bool] | None = None) -> User:
        normalized_email = email.lower().strip()
        user = next((candidate for candidate in self._users if candidate.get_email() == normalized_email), None)
        if user is None:
            raise ValueError("INVALID_CREDENTIALS")

        is_valid_password = password_verifier(user, password) if password_verifier is not None else user.verify_password(password)
        if not is_valid_password:
            raise ValueError("INVALID_CREDENTIALS")

        return user

    def is_email_unique(self, email: str) -> bool:
        normalized_email = email.lower().strip()
        return all(user.get_email() != normalized_email for user in self._users)
