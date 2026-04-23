import math

from app.core.exceptions import bad_request, conflict, forbidden, not_found
from app.domain.event import Event as DomainEvent
from app.domain.event_category import EventCategory as DomainEventCategory
from app.domain.event_manager import EventManager
from app.domain.organizer import Organizer
from app.domain.student import Student
from app.models.event import Event
from app.models.event_save import EventSave
from app.models.user import User
from app.repositories.event_repository import EventRepository
from app.repositories.saved_event_repository import SavedEventRepository
from sqlalchemy.orm import Session


class SavedEventService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)
        self.saved_event_repo = SavedEventRepository(db)

    # ── parse helpers ─────────────────────────────────────────────────────

    def _parse_page(self, page: int | None) -> int:
        if page is None:
            return 1
        if page < 1:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[{"field": "page", "code": "INVALID_QUERY", "detail": "page ต้องมีค่ามากกว่า 0"}],
            )
        return page

    def _parse_page_size(self, page_size: int | None) -> int:
        if page_size is None:
            return 10
        if page_size < 1 or page_size > 100:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[{"field": "pageSize", "code": "INVALID_QUERY", "detail": "pageSize ต้องอยู่ระหว่าง 1 ถึง 100"}],
            )
        return page_size

    def _parse_sort_order(self, sort_order: str | None) -> str:
        if sort_order is None:
            return "asc"
        normalized = sort_order.strip().lower()
        if normalized not in {"asc", "desc"}:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[{"field": "sortOrder", "code": "INVALID_QUERY", "detail": "sortOrder ต้องเป็น asc หรือ desc"}],
            )
        return normalized

    def _parse_sort_by_saved(self, sort_by: str | None) -> str:
        if sort_by is None:
            return "savedAt"
        allowed = {"savedAt", "startTime", "endTime"}
        if sort_by not in allowed:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[{"field": "sortBy", "code": "INVALID_QUERY", "detail": "sortBy ต้องเป็น savedAt, startTime หรือ endTime"}],
            )
        return sort_by

    # ── domain builders ───────────────────────────────────────────────────

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
            short_description=event.short_description,
            location_name=event.location_name,
            latitude=event.latitude,
            longitude=event.longitude,
            start_time=event.start_time,
            end_time=event.end_time,
            cover_image_url=event.cover_image_url,
            category=domain_category,
            organizer=organizer,
        )
        domain_event.set_status(event.status)
        return domain_event

    def _build_domain_student(self, user: User, saved_event_ids: list[int]) -> Student:
        student = Student(
            user_id=user.id,
            name=user.full_name,
            email=user.email,
            password_hash=user.password_hash,
        )
        student._saved_events = saved_event_ids
        return student

    # ── public methods ────────────────────────────────────────────────────

    def get_saved_events(
        self,
        page: int | None,
        page_size: int | None,
        status: str | None,
        sort_by: str | None,
        sort_order: str | None,
        current_user: User,
    ) -> dict:
        if current_user.role != "STUDENT":
            raise forbidden("เฉพาะ STUDENT เท่านั้นที่สามารถดูรายการกิจกรรมที่บันทึกไว้")

        page_number = self._parse_page(page)
        page_size_number = self._parse_page_size(page_size)
        sort_order_value = self._parse_sort_order(sort_order)
        sort_by_field = self._parse_sort_by_saved(sort_by)

        status_filter = None
        if status is not None:
            normalized = status.strip().upper()
            if normalized not in {"DRAFT", "PUBLISHED", "CANCELLED"}:
                raise bad_request(
                    message="ข้อมูล query ไม่ถูกต้อง",
                    errors=[{"field": "status", "code": "INVALID_QUERY", "detail": "status ต้องเป็น DRAFT, PUBLISHED หรือ CANCELLED"}],
                )
            status_filter = normalized

        saved_event_ids = self.saved_event_repo.get_saved_event_ids(current_user.id)
        student = self._build_domain_student(current_user, saved_event_ids)
        domain_saved_ids = student.get_saved_events()

        if not domain_saved_ids:
            return {
                "success": True,
                "message": "ดึงรายการกิจกรรมที่บันทึกไว้สำเร็จ",
                "data": [],
                "meta": {
                    "page": page_number,
                    "pageSize": page_size_number,
                    "totalItems": 0,
                    "totalPages": 1,
                },
            }

        query = self.saved_event_repo.get_saved_events_query(current_user.id)

        if status_filter is not None:
            query = query.filter(Event.status == status_filter)

        if sort_by_field == "savedAt":
            sort_col = EventSave.created_at
        elif sort_by_field == "startTime":
            sort_col = Event.start_time
        else:
            sort_col = Event.end_time

        if sort_order_value == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / page_size_number))
        offset = (page_number - 1) * page_size_number
        event_saves = query.offset(offset).limit(page_size_number).all()

        response_events = []
        for event_save in event_saves:
            orm_event = event_save.event
            response_events.append({
                "eventId": orm_event.id,
                "title": orm_event.title,
                "locationName": orm_event.location_name,
                "latitude": orm_event.latitude,
                "longitude": orm_event.longitude,
                "startTime": orm_event.start_time,
                "endTime": orm_event.end_time,
                "status": orm_event.status,
                "coverImageUrl": orm_event.cover_image_url,
                "category": {
                    "categoryId": orm_event.category.id,
                    "name": orm_event.category.name,
                },
                "organizer": {
                    "userId": orm_event.organizer.id,
                    "fullName": orm_event.organizer.full_name,
                },
                "savedAt": event_save.created_at,
            })

        return {
            "success": True,
            "message": "ดึงรายการกิจกรรมที่บันทึกไว้สำเร็จ",
            "data": response_events,
            "meta": {
                "page": page_number,
                "pageSize": page_size_number,
                "totalItems": total_items,
                "totalPages": total_pages,
            },
        }

    def save_event(self, event_id: int, current_user: User) -> dict:
        if current_user.role != "STUDENT":
            raise forbidden("เฉพาะ STUDENT เท่านั้นที่สามารถบันทึกกิจกรรมได้")

        event = self.event_repo.get_by_id(event_id)
        if event is None:
            raise not_found("ไม่พบกิจกรรม")

        if self.saved_event_repo.is_saved_by_user(event_id, current_user.id):
            raise conflict("กิจกรรมนี้ถูกบันทึกแล้ว")

        domain_event = self._to_domain_event(event)
        manager = EventManager()
        manager.add_event(domain_event)
        domain_event = manager.get_event_by_id(event_id)

        student = self._build_domain_student(current_user, self.saved_event_repo.get_saved_event_ids(current_user.id))
        student.save_event(domain_event)

        self.saved_event_repo.create_saved_event(event_id, current_user.id)

        return {
            "success": True,
            "message": "บันทึกกิจกรรมสำเร็จ",
            "data": {
                "eventId": event_id,
                "saved": True,
            },
        }

    def check_saved_event(self, event_id: int, current_user: User) -> dict:
        if current_user.role != "STUDENT":
            raise forbidden("เฉพาะ STUDENT เท่านั้นที่สามารถตรวจสอบสถานะการบันทึกได้")

        event = self.event_repo.get_by_id(event_id)
        if event is None:
            raise not_found("ไม่พบกิจกรรม")

        saved_event_ids = self.saved_event_repo.get_saved_event_ids(current_user.id)
        student = self._build_domain_student(current_user, saved_event_ids)
        domain_event = self._to_domain_event(event)
        is_saved = student.has_saved_event(domain_event)

        return {
            "success": True,
            "message": "ตรวจสอบสถานะการบันทึกสำเร็จ",
            "data": {
                "eventId": event_id,
                "isSaved": is_saved,
                "title": event.title,
                "status": event.status,
                "coverImageUrl": event.cover_image_url,
            },
        }

    def unsave_event(self, event_id: int, current_user: User) -> dict:
        if current_user.role != "STUDENT":
            raise forbidden("เฉพาะ STUDENT เท่านั้นที่สามารถยกเลิกบันทึกกิจกรรมได้")

        event_save = self.saved_event_repo.get_saved_event(event_id, current_user.id)
        if event_save is None:
            raise not_found("ไม่พบกิจกรรมที่บันทึกไว้")

        domain_event = self._to_domain_event(event_save.event)
        student = self._build_domain_student(current_user, self.saved_event_repo.get_saved_event_ids(current_user.id))
        student.unsave_event(domain_event)

        self.saved_event_repo.delete_saved_event(event_save)

        return {
            "success": True,
            "message": "ยกเลิกบันทึกกิจกรรมสำเร็จ",
            "data": {
                "eventId": event_id,
                "saved": False,
            },
        }
