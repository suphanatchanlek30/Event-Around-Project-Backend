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
        short_description: str | None,
        location_name: str,
        latitude: float,
        longitude: float,
        start_time: datetime,
        end_time: datetime,
        cover_image_url: str | None,
        category: EventCategory,
        organizer: Organizer,
    ):
        self._event_id = event_id
        self._title = title
        self._description = description
        self._short_description = short_description
        self._location_name = location_name
        self._latitude = latitude
        self._longitude = longitude
        self._start_time = start_time
        self._end_time = end_time
        self._cover_image_url = cover_image_url
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

    def get_location_name(self) -> str:
        return self._location_name

    def get_latitude(self) -> float:
        return self._latitude

    def get_longitude(self) -> float:
        return self._longitude

    def get_start_time(self) -> datetime:
        return self._start_time

    def set_start_time(self, start_time: datetime) -> None:
        self._start_time = start_time

    def get_end_time(self) -> datetime:
        return self._end_time

    def set_end_time(self, end_time: datetime) -> None:
        self._end_time = end_time

    def get_status(self) -> str:
        return self._status

    def set_status(self, status: str) -> None:
        self._status = status

    def get_short_description(self) -> str | None:
        return self._short_description

    def get_cover_image_url(self) -> str | None:
        return self._cover_image_url

    def get_category(self) -> EventCategory:
        return self._category

    def get_organizer(self) -> Organizer:
        return self._organizer

    def set_category(self, category: EventCategory) -> None:
        self._category = category

    def is_active(self, current_time: datetime) -> bool:
        return (
            self._status == "PUBLISHED"
            and self._start_time <= current_time
            and current_time <= self._end_time
        )

    def validate_time_range(self) -> bool:
        return self._start_time < self._end_time

    def update_location(self, location_name: str, latitude: float, longitude: float) -> None:
        self._location_name = location_name
        self._latitude = latitude
        self._longitude = longitude
