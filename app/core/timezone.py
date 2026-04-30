from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

from app.core.settings import settings
from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

DEFAULT_APP_TIMEZONE = "Asia/Bangkok"


class UTCDateTime(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return normalize_datetime_for_storage(value, assume_timezone=UTC)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return ensure_timezone_aware(value, UTC).astimezone(UTC)


@lru_cache(maxsize=1)
def get_app_timezone() -> ZoneInfo:
    timezone_name = settings.app_timezone or DEFAULT_APP_TIMEZONE
    return ZoneInfo(timezone_name)


def get_now_utc() -> datetime:
    return datetime.now(UTC)


def get_now_bangkok() -> datetime:
    return get_now_utc().astimezone(get_app_timezone())


def ensure_timezone_aware(value: datetime, default_timezone: ZoneInfo | None = None) -> datetime:
    timezone = default_timezone or get_app_timezone()
    if value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone)


def parse_datetime_input(value: str | datetime, assume_timezone: ZoneInfo | None = None) -> datetime:
    parsed = value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        parsed = datetime.fromisoformat(normalized)

    timezone = assume_timezone or get_app_timezone()
    return normalize_datetime_for_storage(parsed, assume_timezone=timezone)


def convert_bangkok_to_utc(value: datetime) -> datetime:
    return ensure_timezone_aware(value, get_app_timezone()).astimezone(UTC)


def convert_utc_to_bangkok(value: datetime) -> datetime:
    return ensure_timezone_aware(value, UTC).astimezone(get_app_timezone())


def normalize_datetime_for_storage(value: datetime, assume_timezone: ZoneInfo | None = None) -> datetime:
    timezone = assume_timezone or UTC
    return ensure_timezone_aware(value, timezone).astimezone(UTC)


def format_datetime_for_api(value: datetime | None) -> str | None:
    if value is None:
        return None
    return convert_utc_to_bangkok(value).isoformat()


def serialize_datetime_payload(value: Any) -> Any:
    if isinstance(value, datetime):
        return format_datetime_for_api(value)
    if isinstance(value, list):
        return [serialize_datetime_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(serialize_datetime_payload(item) for item in value)
    if isinstance(value, dict):
        return {key: serialize_datetime_payload(item) for key, item in value.items()}
    return value