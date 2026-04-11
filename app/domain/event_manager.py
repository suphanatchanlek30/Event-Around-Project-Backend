from __future__ import annotations

from datetime import datetime

from app.domain.event import Event


class EventManager:
    def __init__(self):
        self._events: list[Event] = []

    def add_event(self, event: Event) -> None:
        self._events.append(event)

    def update_event(self, event_id: int, new_data: dict) -> None:
        for event in self._events:
            if event.get_event_id() == event_id:
                for key, value in new_data.items():
                    if hasattr(event, f"set_{key}"):
                        getattr(event, f"set_{key}")(value)
                return

    def delete_event(self, event_id: int) -> None:
        self._events = [event for event in self._events if event.get_event_id() != event_id]

    def get_event_by_id(self, event_id: int) -> Event:
        for event in self._events:
            if event.get_event_id() == event_id:
                return event
        raise ValueError("Event not found")

    def get_all_events(self) -> list[Event]:
        return list(self._events)

    def get_active_events(self, current_time: datetime) -> list[Event]:
        return [event for event in self._events if event.is_active(current_time)]

    def search_by_keyword(self, keyword: str) -> list[Event]:
        normalized = keyword.strip().lower()
        return [
            event
            for event in self._events
            if normalized in event.get_title().lower()
            or normalized in event.get_description().lower()
        ]

    def filter_by_category(self, category_id: int) -> list[Event]:
        return [
            event
            for event in self._events
            if event.get_category().get_category_id() == category_id
        ]

    def get_nearby_events(self, user_lat: float, user_lon: float, radius_km: float) -> list[Event]:
        raise NotImplementedError("get_nearby_events is not implemented in skeleton phase.")

    def sort_events_by_distance(self, user_lat: float, user_lon: float) -> list[Event]:
        raise NotImplementedError("sort_events_by_distance is not implemented in skeleton phase.")
