from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.user import User

if TYPE_CHECKING:
    from app.domain.event import Event


class Organizer(User):
    def __init__(self, user_id: int, name: str, email: str, password_hash: str):
        super().__init__(user_id=user_id, name=name, email=email, password_hash=password_hash)
        self._organized_events: list = []

    def get_organized_events(self) -> list:
        return self._organized_events

    def create_event(self, event: Event) -> None:
        raise NotImplementedError("create_event is not implemented in skeleton phase.")

    def remove_event(self, event: Event) -> None:
        raise NotImplementedError("remove_event is not implemented in skeleton phase.")

    def can_edit_event(self, event: Event) -> bool:
        raise NotImplementedError("can_edit_event is not implemented in skeleton phase.")

    def get_role(self) -> str:
        return "ORGANIZER"
