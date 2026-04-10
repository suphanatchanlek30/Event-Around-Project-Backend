from __future__ import annotations

from app.domain.auth_manager import AuthManager
from app.domain.event import Event
from app.domain.event_manager import EventManager
from app.domain.location_service import LocationService
from app.domain.user import User


class EventAroundSystem:
    def __init__(self, auth_manager: AuthManager, event_manager: EventManager, location_service: LocationService):
        self._auth_manager = auth_manager
        self._event_manager = event_manager
        self._location_service = location_service
        self._current_user: User | None = None

    def login(self, email: str, password: str) -> bool:
        raise NotImplementedError("login is not implemented in skeleton phase.")

    def logout(self) -> None:
        raise NotImplementedError("logout is not implemented in skeleton phase.")

    def detect_user_location(self) -> tuple[float, float]:
        raise NotImplementedError("detect_user_location is not implemented in skeleton phase.")

    def show_nearby_events(self, user_lat: float, user_lon: float, radius_km: float) -> list[Event]:
        raise NotImplementedError("show_nearby_events is not implemented in skeleton phase.")

    def create_event(self, event_data: dict) -> Event:
        raise NotImplementedError("create_event is not implemented in skeleton phase.")

    def save_event_for_current_user(self, event_id: int) -> None:
        raise NotImplementedError("save_event_for_current_user is not implemented in skeleton phase.")
