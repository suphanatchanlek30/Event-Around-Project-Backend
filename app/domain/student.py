from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.user import User

if TYPE_CHECKING:
    from app.domain.event import Event


class Student(User):
    def __init__(self, user_id: int, name: str, email: str, password_hash: str):
        super().__init__(user_id=user_id, name=name, email=email, password_hash=password_hash)
        self._saved_events: list[int] = []

    def get_saved_events(self) -> list[int]:
        return self._saved_events

    def save_event(self, event: "Event") -> None:
        if event.get_event_id() not in self._saved_events:
            self._saved_events.append(event.get_event_id())

    def unsave_event(self, event: "Event") -> None:
        self._saved_events = [saved_id for saved_id in self._saved_events if saved_id != event.get_event_id()]

    def has_saved_event(self, event: "Event") -> bool:
        return event.get_event_id() in self._saved_events

    def get_role(self) -> str:
        return "STUDENT"
