import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request
from app.domain.event import Event as DomainEvent
from app.domain.event_category import EventCategory as DomainEventCategory
from app.domain.event_manager import EventManager
from app.domain.organizer import Organizer
from app.models.event import Event
from app.repositories.event_repository import EventRepository


class EventService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)

    def _parse_page(self, page: int | None) -> int:
        if page is None:
            return 1
        if page < 1:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[
                    {
                        "field": "page",
                        "code": "INVALID_QUERY",
                        "detail": "page ต้องมีค่ามากกว่า 0",
                    }
                ],
            )
        return page

    def _parse_page_size(self, page_size: int | None) -> int:
        if page_size is None:
            return 10
        if page_size < 1 or page_size > 100:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[
                    {
                        "field": "pageSize",
                        "code": "INVALID_QUERY",
                        "detail": "pageSize ต้องอยู่ระหว่าง 1 ถึง 100",
                    }
                ],
            )
        return page_size

    def _parse_sort_by(self, sort_by: str | None) -> str:
        if sort_by is None:
            return "startTime"

        allowed = {"startTime", "endTime", "createdAt"}
        if sort_by not in allowed:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[
                    {
                        "field": "sortBy",
                        "code": "INVALID_QUERY",
                        "detail": "sortBy ต้องเป็น startTime, endTime หรือ createdAt",
                    }
                ],
            )
        return sort_by

    def _parse_sort_order(self, sort_order: str | None) -> str:
        if sort_order is None:
            return "asc"
        normalized = sort_order.strip().lower()
        if normalized not in {"asc", "desc"}:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[
                    {
                        "field": "sortOrder",
                        "code": "INVALID_QUERY",
                        "detail": "sortOrder ต้องเป็น asc หรือ desc",
                    }
                ],
            )
        return normalized

    def _parse_status(self, status: str | None) -> str | None:
        if status is None:
            return "PUBLISHED"
        normalized = status.strip().upper()
        if normalized not in {"DRAFT", "PUBLISHED", "CANCELLED"}:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[
                    {
                        "field": "status",
                        "code": "INVALID_QUERY",
                        "detail": "status ต้องเป็น DRAFT, PUBLISHED หรือ CANCELLED",
                    }
                ],
            )
        return normalized

    def _parse_datetime(self, value: str | None, field_name: str) -> datetime | None:
        if value is None:
            return None

        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[
                    {
                        "field": field_name,
                        "code": "INVALID_QUERY",
                        "detail": f"{field_name} ต้องเป็นรูปแบบ ISO 8601",
                    }
                ],
            )

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)

        return parsed

    def _to_domain_event(self, event: Event) -> DomainEvent:
        domain_category = DomainEventCategory(
            category_id=event.category.id,
            name=event.category.name,
            description=event.category.description,
            is_active=event.category.is_active,
        )
        organizer = Organizer(
            user_id=event.organizer.id,
            name=event.organizer.full_name,
            email=event.organizer.email,
            password_hash=event.organizer.password_hash,
        )
        domain_event = DomainEvent(
            event_id=event.id,
            title=event.title,
            description=event.description or "",
            location_name=event.location_name,
            latitude=event.latitude,
            longitude=event.longitude,
            start_time=event.start_time,
            end_time=event.end_time,
            category=domain_category,
            organizer=organizer,
        )
        domain_event.set_status(event.status)
        return domain_event

    def _to_response_data(self, event: DomainEvent) -> dict:
        return {
            "eventId": event.get_event_id(),
            "title": event.get_title(),
            "locationName": event.get_location_name(),
            "startTime": event.get_start_time(),
            "endTime": event.get_end_time(),
            "status": event.get_status(),
            "category": {
                "categoryId": event.get_category().get_category_id(),
                "name": event.get_category().get_name(),
            },
            "organizer": {
                "userId": event.get_organizer().get_user_id(),
                "fullName": event.get_organizer().get_name(),
            },
        }

    def list_events(
        self,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
        category_id: int | None = None,
        status: str | None = None,
        start_from: str | None = None,
        end_to: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> dict:
        page_number = self._parse_page(page)
        page_size_number = self._parse_page_size(page_size)
        sort_by_field = self._parse_sort_by(sort_by)
        sort_order_value = self._parse_sort_order(sort_order)
        status_filter = self._parse_status(status)
        start_dt = self._parse_datetime(start_from, "startFrom")
        end_dt = self._parse_datetime(end_to, "endTo")

        query = self.event_repo.list_events(
            status=status_filter,
            start_from=start_dt,
            end_to=end_dt,
        )

        orm_events = query.all()
        manager = EventManager()
        for orm_event in orm_events:
            manager.add_event(self._to_domain_event(orm_event))

        filtered_events = manager.get_all_events()
        if search is not None:
            filtered_events = manager.search_by_keyword(search)

        if category_id is not None:
            filtered_events = [
                event for event in filtered_events if event.get_category().get_category_id() == category_id
            ]

        sort_key_map = {
            "startTime": lambda item: item.get_start_time(),
            "endTime": lambda item: item.get_end_time(),
            "createdAt": lambda item: item.get_start_time(),
        }
        reverse = sort_order_value == "desc"
        sorted_events = sorted(filtered_events, key=sort_key_map[sort_by_field], reverse=reverse)

        total_items = len(sorted_events)
        total_pages = max(1, math.ceil(total_items / page_size_number))
        start_index = (page_number - 1) * page_size_number
        end_index = start_index + page_size_number
        paged_events = sorted_events[start_index:end_index]

        response_events = [self._to_response_data(event) for event in paged_events]

        return {
            "success": True,
            "message": "ดึงรายการกิจกรรมสำเร็จ",
            "data": response_events,
            "meta": {
                "page": page_number,
                "pageSize": page_size_number,
                "totalItems": total_items,
                "totalPages": total_pages,
            },
        }
