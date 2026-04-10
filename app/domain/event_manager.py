from __future__ import annotations

from datetime import datetime

from app.domain.event import Event


class EventManager:
    def __init__(self):
        self._events: list[Event] = []

    def add_event(self, event: Event) -> None:
        raise NotImplementedError("add_event is not implemented in skeleton phase.")

    def update_event(self, event_id: int, new_data: dict) -> None:
        raise NotImplementedError("update_event is not implemented in skeleton phase.")

    def delete_event(self, event_id: int) -> None:
        raise NotImplementedError("delete_event is not implemented in skeleton phase.")

    def get_event_by_id(self, event_id: int) -> Event:
        raise NotImplementedError("get_event_by_id is not implemented in skeleton phase.")

    def get_all_events(self) -> list[Event]:
        raise NotImplementedError("get_all_events is not implemented in skeleton phase.")

    def get_active_events(self, current_time: datetime) -> list[Event]:
        raise NotImplementedError("get_active_events is not implemented in skeleton phase.")

    def search_by_keyword(self, keyword: str) -> list[Event]:
        raise NotImplementedError("search_by_keyword is not implemented in skeleton phase.")

    def filter_by_category(self, category_name: str) -> list[Event]:
        raise NotImplementedError("filter_by_category is not implemented in skeleton phase.")

    def get_nearby_events(self, user_lat: float, user_lon: float, radius_km: float) -> list[Event]:
        raise NotImplementedError("get_nearby_events is not implemented in skeleton phase.")

    def sort_events_by_distance(self, user_lat: float, user_lon: float) -> list[Event]:
        raise NotImplementedError("sort_events_by_distance is not implemented in skeleton phase.")
