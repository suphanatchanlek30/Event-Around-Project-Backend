from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.user import User

if TYPE_CHECKING:
    from app.domain.event import Event


class Student(User):
    def __init__(self, user_id: int, name: str, email: str, password_hash: str):
        super().__init__(user_id=user_id, name=name, email=email, password_hash=password_hash)
        self._saved_events: list = []

    def get_saved_events(self) -> list:
        return self._saved_events

    def save_event(self, event: "Event") -> None:
        raise NotImplementedError("save_event is not implemented in skeleton phase.")

    def unsave_event(self, event: "Event") -> None:
        raise NotImplementedError("unsave_event is not implemented in skeleton phase.")

    def has_saved_event(self, event: "Event") -> bool:
        raise NotImplementedError("has_saved_event is not implemented in skeleton phase.")

    def get_role(self) -> str:
        return "STUDENT"
