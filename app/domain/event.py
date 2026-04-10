from __future__ import annotations

from datetime import datetime

from app.domain.event_category import EventCategory
from app.domain.organizer import Organizer


class Event:
    def __init__(
        self,
        event_id: int,
        title: str,
        description: str,
        location_name: str,
        latitude: float,
        longitude: float,
        start_time: datetime,
        end_time: datetime,
        category: EventCategory,
        organizer: Organizer,
    ):
        self._event_id = event_id
        self._title = title
        self._description = description
        self._location_name = location_name
        self._latitude = latitude
        self._longitude = longitude
        self._start_time = start_time
        self._end_time = end_time
        self._status = "DRAFT"
        self._category = category
        self._organizer = organizer

    def get_event_id(self) -> int:
        return self._event_id

    def get_title(self) -> str:
        return self._title

    def set_title(self, title: str) -> None:
        self._title = title

    def get_description(self) -> str:
        return self._description

    def set_description(self, description: str) -> None:
        self._description = description

    def get_status(self) -> str:
        return self._status

    def set_status(self, status: str) -> None:
        self._status = status

    def get_category(self) -> EventCategory:
        return self._category

    def set_category(self, category: EventCategory) -> None:
        self._category = category

    def is_active(self, current_time: datetime) -> bool:
        raise NotImplementedError("is_active is not implemented in skeleton phase.")

    def validate_time_range(self) -> bool:
        raise NotImplementedError("validate_time_range is not implemented in skeleton phase.")

    def update_location(self, location_name: str, latitude: float, longitude: float) -> None:
        raise NotImplementedError("update_location is not implemented in skeleton phase.")
