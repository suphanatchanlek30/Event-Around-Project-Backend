import csv
import io
import math
from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import bad_request, conflict, forbidden, not_found
from app.domain.event import Event as DomainEvent
from app.domain.event_category import EventCategory as DomainEventCategory
from app.domain.event_manager import EventManager
from app.domain.location_service import LocationService
from app.domain.organizer import Organizer
from app.domain.student import Student
from app.models.event import Event
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.event_import_log_repository import EventImportLogRepository
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventImportRequest
from fastapi import UploadFile
from sqlalchemy.orm import Session


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
            ) from None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        else:
            parsed = parsed.astimezone(UTC)

        return parsed

    def _parse_event_status(self, status: str | None, current_user: User) -> str:
        if status is None:
            return "DRAFT"

        normalized = status.strip().upper()
        if normalized not in {"DRAFT", "PUBLISHED"}:
            raise bad_request(
                message="ข้อมูลไม่ถูกต้อง",
                errors=[
                    {
                        "field": "status",
                        "code": "INVALID_STATUS",
                        "detail": "status ต้องเป็น DRAFT หรือ PUBLISHED",
                    }
                ],
            )

        if normalized == "PUBLISHED" and current_user.role != "ADMIN":
            raise forbidden("เฉพาะ ADMIN เท่านั้นที่สามารถสร้างกิจกรรมเป็น PUBLISHED ได้")

        return normalized

    def _parse_import_status(self, status: str | None, current_user: User) -> str:
        if status is None or not status.strip():
            return "DRAFT"

        normalized = status.strip().upper()
        if normalized not in {"DRAFT", "PUBLISHED"}:
            raise bad_request(
                message="ข้อมูลไม่ถูกต้อง",
                errors=[
                    {
                        "field": "defaultStatus",
                        "code": "INVALID_STATUS",
                        "detail": "defaultStatus ต้องเป็น DRAFT หรือ PUBLISHED",
                    }
                ],
            )

        if normalized == "PUBLISHED" and current_user.role != "ADMIN":
            raise forbidden("เฉพาะ ADMIN เท่านั้นที่สามารถสร้างกิจกรรมเป็น PUBLISHED ได้")

        return normalized

    def _validate_import_headers(self, headers: list[str] | None) -> bool:
        if headers is None:
            return False

        required_headers = {
            "title",
            "locationName",
            "latitude",
            "longitude",
            "startTime",
            "endTime",
            "categoryId",
        }
        found_headers = {header.strip() for header in headers if header}
        return required_headers.issubset(found_headers)

    def _parse_import_row(self, raw_row: dict[str, str], row_number: int, default_status: str, current_user: User) -> tuple[dict | None, list[dict]]:
        errors: list[dict] = []

        def get_value(field: str) -> str:
            return (raw_row.get(field) or "").strip()

        title = get_value("title")
        description = get_value("description") or None
        short_description = get_value("shortDescription") or None
        location_name = get_value("locationName")
        latitude_value = get_value("latitude")
        longitude_value = get_value("longitude")
        start_time_value = get_value("startTime")
        end_time_value = get_value("endTime")
        category_id_value = get_value("categoryId")
        cover_image_url = get_value("coverImageUrl") or None
        status_value = get_value("status")

        if not title:
            errors.append({"row": row_number, "field": "title", "detail": "title ต้องระบุ"})
        if not location_name:
            errors.append({"row": row_number, "field": "locationName", "detail": "locationName ต้องระบุ"})

        latitude = None
        if not latitude_value:
            errors.append({"row": row_number, "field": "latitude", "detail": "latitude ต้องระบุ"})
        else:
            try:
                latitude = float(latitude_value)
            except ValueError:
                errors.append({"row": row_number, "field": "latitude", "detail": "latitude ต้องเป็นตัวเลข"})

        longitude = None
        if not longitude_value:
            errors.append({"row": row_number, "field": "longitude", "detail": "longitude ต้องระบุ"})
        else:
            try:
                longitude = float(longitude_value)
            except ValueError:
                errors.append({"row": row_number, "field": "longitude", "detail": "longitude ต้องเป็นตัวเลข"})

        start_time = None
        if not start_time_value:
            errors.append({"row": row_number, "field": "startTime", "detail": "startTime ต้องระบุ"})
        else:
            try:
                start_time = datetime.fromisoformat(start_time_value)
            except ValueError:
                errors.append({"row": row_number, "field": "startTime", "detail": "Invalid datetime"})

        end_time = None
        if not end_time_value:
            errors.append({"row": row_number, "field": "endTime", "detail": "endTime ต้องระบุ"})
        else:
            try:
                end_time = datetime.fromisoformat(end_time_value)
            except ValueError:
                errors.append({"row": row_number, "field": "endTime", "detail": "Invalid datetime"})

        category_id = None
        if not category_id_value:
            errors.append({"row": row_number, "field": "categoryId", "detail": "categoryId ต้องระบุ"})
        else:
            try:
                category_id = int(category_id_value)
            except ValueError:
                errors.append({"row": row_number, "field": "categoryId", "detail": "categoryId ต้องเป็นจำนวนเต็ม"})

        if category_id is not None:
            if CategoryRepository(self.db).get_by_id(category_id) is None:
                errors.append({"row": row_number, "field": "categoryId", "detail": "ไม่พบหมวดหมู่ที่ต้องการ"})

        if latitude is not None and longitude is not None:
            if not LocationService().validate_coordinates(latitude, longitude):
                errors.append({"row": row_number, "field": "latitude/longitude", "detail": "Invalid coordinates"})

        if start_time is not None and end_time is not None:
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=UTC)
            else:
                start_time = start_time.astimezone(UTC)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=UTC)
            else:
                end_time = end_time.astimezone(UTC)
            if start_time >= end_time:
                errors.append({"row": row_number, "field": "startTime/endTime", "detail": "startTime ต้องน้อยกว่า endTime"})

        status = default_status
        if status_value:
            normalized_status = status_value.strip().upper()
            if normalized_status not in {"DRAFT", "PUBLISHED"}:
                errors.append({"row": row_number, "field": "status", "detail": "status ต้องเป็น DRAFT หรือ PUBLISHED"})
            else:
                if normalized_status == "PUBLISHED" and current_user.role != "ADMIN":
                    errors.append({"row": row_number, "field": "status", "detail": "เฉพาะ ADMIN เท่านั้นที่สามารถตั้ง status เป็น PUBLISHED ได้"})
                else:
                    status = normalized_status

        if errors:
            return None, errors

        return (
            {
                "title": title,
                "description": description,
                "short_description": short_description,
                "location_name": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "start_time": start_time,
                "end_time": end_time,
                "category_id": category_id,
                "cover_image_url": cover_image_url,
                "status": status,
            },
            [],
        )

    def _parse_import_item(self, item: Any, row_number: int, current_user: User) -> tuple[dict | None, list[dict]]:
        errors: list[dict] = []

        title = item.title.strip() if item.title else ""
        description = item.description or None
        short_description = item.short_description
        location_name = item.location_name.strip() if item.location_name else ""
        latitude = item.latitude
        longitude = item.longitude
        start_time = item.start_time
        end_time = item.end_time
        category_id = item.category_id
        cover_image_url = item.cover_image_url or None
        status_value = item.status

        if not title:
            errors.append({"row": row_number, "field": "title", "detail": "title ต้องระบุ"})
        if not location_name:
            errors.append({"row": row_number, "field": "locationName", "detail": "locationName ต้องระบุ"})

        if latitude is None:
            errors.append({"row": row_number, "field": "latitude", "detail": "latitude ต้องระบุ"})
        if longitude is None:
            errors.append({"row": row_number, "field": "longitude", "detail": "longitude ต้องระบุ"})

        if latitude is not None and longitude is not None:
            if not LocationService().validate_coordinates(latitude, longitude):
                errors.append({"row": row_number, "field": "latitude/longitude", "detail": "Invalid coordinates"})

        if start_time is None:
            errors.append({"row": row_number, "field": "startTime", "detail": "startTime ต้องระบุ"})
        if end_time is None:
            errors.append({"row": row_number, "field": "endTime", "detail": "endTime ต้องระบุ"})

        if start_time is not None and end_time is not None:
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=UTC)
            else:
                start_time = start_time.astimezone(UTC)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=UTC)
            else:
                end_time = end_time.astimezone(UTC)
            if start_time >= end_time:
                errors.append({"row": row_number, "field": "startTime/endTime", "detail": "startTime ต้องน้อยกว่า endTime"})

        if category_id is None:
            errors.append({"row": row_number, "field": "categoryId", "detail": "categoryId ต้องระบุ"})
        else:
            if CategoryRepository(self.db).get_by_id(category_id) is None:
                errors.append({"row": row_number, "field": "categoryId", "detail": "ไม่พบหมวดหมู่ที่ต้องการ"})

        status = "DRAFT"
        if status_value:
            normalized_status = status_value.strip().upper()
            if normalized_status not in {"DRAFT", "PUBLISHED"}:
                errors.append({"row": row_number, "field": "status", "detail": "status ต้องเป็น DRAFT หรือ PUBLISHED"})
            else:
                if normalized_status == "PUBLISHED" and current_user.role != "ADMIN":
                    errors.append({"row": row_number, "field": "status", "detail": "เฉพาะ ADMIN เท่านั้นที่สามารถตั้ง status เป็น PUBLISHED ได้"})
                else:
                    status = normalized_status

        if errors:
            return None, errors

        return (
            {
                "title": title,
                "description": description,
                "short_description": short_description,
                "location_name": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "start_time": start_time,
                "end_time": end_time,
                "category_id": category_id,
                "cover_image_url": cover_image_url,
                "status": status,
            },
            [],
        )

    def import_events_from_csv(self, file: UploadFile, default_status: str | None, current_user: User) -> dict:
        self._ensure_admin_or_organizer(current_user)

        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise bad_request(
                message="ไฟล์ต้องเป็น CSV",
                errors=[
                    {
                        "field": "file",
                        "code": "INVALID_FILE",
                        "detail": "ต้องอัปโหลดไฟล์ .csv",
                    }
                ],
            )

        normalized_default_status = self._parse_import_status(default_status, current_user)

        try:
            csv_stream = io.TextIOWrapper(file.file, encoding="utf-8-sig")
            reader = csv.DictReader(csv_stream)
        except Exception:
            raise bad_request(
                message="ไฟล์ CSV ไม่ถูกต้อง",
                errors=[
                    {
                        "field": "file",
                        "code": "INVALID_CSV_FORMAT",
                        "detail": "ไม่สามารถอ่านไฟล์ CSV ได้",
                    }
                ],
            ) from None

        if not self._validate_import_headers(reader.fieldnames):
            raise bad_request(
                message="ไฟล์ CSV ไม่ถูกต้อง",
                errors=[
                    {
                        "field": "file",
                        "code": "INVALID_CSV_FORMAT",
                        "detail": "header CSV ต้องมี title, locationName, latitude, longitude, startTime, endTime, categoryId",
                    }
                ],
            )

        total_records = 0
        success_records = 0
        failed_records = 0
        errors: list[dict] = []

        for row_index, row in enumerate(reader, start=2):
            total_records += 1
            parsed, row_errors = self._parse_import_row(row, row_index, normalized_default_status, current_user)
            if row_errors:
                failed_records += 1
                errors.extend(row_errors)
                continue

            try:
                self.event_repo.create(
                    title=parsed["title"],
                    description=parsed["description"],
                    short_description=parsed["short_description"],
                    location_name=parsed["location_name"],
                    latitude=parsed["latitude"],
                    longitude=parsed["longitude"],
                    start_time=parsed["start_time"],
                    end_time=parsed["end_time"],
                    status=parsed["status"],
                    category_id=parsed["category_id"],
                    organizer_id=current_user.id,
                    cover_image_url=parsed["cover_image_url"],
                )
                success_records += 1
            except Exception:
                self.db.rollback()
                failed_records += 1
                errors.append({"row": row_index, "field": "csv", "detail": "ไม่สามารถบันทึกกิจกรรมได้"})

        import_log = EventImportLogRepository(self.db).create(
            organizer_id=current_user.id,
            total_records=total_records,
            success_records=success_records,
            failed_records=failed_records,
            default_status=normalized_default_status,
            file_name=file.filename,
        )

        return {
            "success": True,
            "message": "นำเข้าข้อมูล CSV สำเร็จ",
            "data": {
                "totalRecords": total_records,
                "successRecords": success_records,
                "failedRecords": failed_records,
                "importLogId": import_log.id,
                "errors": errors,
            },
        }

    def import_events_from_json(self, payload: EventImportRequest, current_user: User) -> dict:
        self._ensure_admin_or_organizer(current_user)

        total_records = 0
        success_records = 0
        failed_records = 0
        errors: list[dict] = []

        for row_index, item in enumerate(payload.events, start=1):
            total_records += 1
            parsed, row_errors = self._parse_import_item(item, row_index, current_user)
            if row_errors:
                failed_records += 1
                errors.extend(row_errors)
                continue

            try:
                self.event_repo.create(
                    title=parsed["title"],
                    description=parsed["description"],
                    short_description=parsed["short_description"],
                    location_name=parsed["location_name"],
                    latitude=parsed["latitude"],
                    longitude=parsed["longitude"],
                    start_time=parsed["start_time"],
                    end_time=parsed["end_time"],
                    status=parsed["status"],
                    category_id=parsed["category_id"],
                    organizer_id=current_user.id,
                    cover_image_url=parsed["cover_image_url"],
                )
                success_records += 1
            except Exception:
                self.db.rollback()
                failed_records += 1
                errors.append({"row": row_index, "field": "json", "detail": "ไม่สามารถบันทึกกิจกรรมได้"})

        import_log = EventImportLogRepository(self.db).create(
            organizer_id=current_user.id,
            total_records=total_records,
            success_records=success_records,
            failed_records=failed_records,
            default_status=None,
            file_name=None,
        )

        return {
            "success": True,
            "message": "นำเข้าข้อมูล JSON สำเร็จ",
            "data": {
                "totalRecords": total_records,
                "successRecords": success_records,
                "failedRecords": failed_records,
                "importLogId": import_log.id,
                "errors": errors,
            },
        }

    def _validate_coordinates(self, latitude: float, longitude: float) -> None:
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise bad_request(
                message="ข้อมูลพิกัดไม่ถูกต้อง",
                errors=[
                    {
                        "field": "latitude/longitude",
                        "code": "INVALID_COORDINATES",
                        "detail": "latitude ต้องอยู่ระหว่าง -90 ถึง 90 และ longitude ต้องอยู่ระหว่าง -180 ถึง 180",
                    }
                ],
            )

    def _ensure_category_exists(self, category_id: int):
        category = CategoryRepository(self.db).get_by_id(category_id)
        if category is None:
            raise not_found("ไม่พบหมวดหมู่ที่ต้องการ")
        return category

    def _ensure_event_owner(self, event: Event, current_user: User) -> None:
        if current_user.role == "ADMIN":
            return

        if current_user.role == "ORGANIZER" and event.organizer_id == current_user.id:
            return

        raise forbidden("ไม่มีสิทธิ์แก้ไขกิจกรรมนี้")

    def _ensure_admin(self, current_user: User) -> None:
        if current_user.role != "ADMIN":
            raise forbidden("เฉพาะ ADMIN เท่านั้นที่สามารถดำเนินการนี้ได้")

    def _ensure_publishable(self, event: Event) -> None:
        required_fields = [
            ("title", event.title),
            ("locationName", event.location_name),
            ("startTime", event.start_time),
            ("endTime", event.end_time),
            ("categoryId", event.category_id),
        ]
        missing = [field for field, value in required_fields if value is None or (isinstance(value, str) and value.strip() == "")]
        if missing:
            raise bad_request(
                message="ข้อมูลกิจกรรมไม่ครบ",
                errors=[
                    {
                        "field": ", ".join(missing),
                        "code": "INCOMPLETE_EVENT_DATA",
                        "detail": "กิจกรรมต้องมี title, locationName, startTime, endTime และ categoryId ก่อนเผยแพร่",
                    }
                ],
            )

        if event.start_time is None or event.end_time is None or event.start_time >= event.end_time:
            raise bad_request(
                message="ช่วงเวลาของกิจกรรมไม่ถูกต้อง",
                errors=[
                    {
                        "field": "startTime/endTime",
                        "code": "INVALID_TIME_RANGE",
                        "detail": "startTime ต้องน้อยกว่า endTime",
                    }
                ],
            )

        if not LocationService().validate_coordinates(event.latitude, event.longitude):
            raise bad_request(
                message="ข้อมูลพิกัดไม่ถูกต้อง",
                errors=[
                    {
                        "field": "latitude/longitude",
                        "code": "INVALID_COORDINATES",
                        "detail": "latitude ต้องอยู่ระหว่าง -90 ถึง 90 และ longitude ต้องอยู่ระหว่าง -180 ถึง 180",
                    }
                ],
            )

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

    def _to_response_data(self, event: DomainEvent) -> dict:
        return {
            "eventId": event.get_event_id(),
            "title": event.get_title(),
            "description": event.get_description(),
            "shortDescription": event.get_short_description(),
            "locationName": event.get_location_name(),
            "startTime": event.get_start_time(),
            "endTime": event.get_end_time(),
            "status": event.get_status(),
            "coverImageUrl": event.get_cover_image_url(),
            "category": {
                "categoryId": event.get_category().get_category_id(),
                "name": event.get_category().get_name(),
            },
            "organizer": {
                "userId": event.get_organizer().get_user_id(),
                "fullName": event.get_organizer().get_name(),
            },
        }

    def _to_detail_response(
        self,
        event: DomainEvent,
        saved_count: int,
        is_saved: bool,
        cancel_reason: str | None,
    ) -> dict:
        return {
            "eventId": event.get_event_id(),
            "title": event.get_title(),
            "description": event.get_description(),
            "shortDescription": event.get_short_description(),
            "locationName": event.get_location_name(),
            "latitude": event.get_latitude(),
            "longitude": event.get_longitude(),
            "startTime": event.get_start_time(),
            "endTime": event.get_end_time(),
            "status": event.get_status(),
            "cancelReason": cancel_reason,
            "coverImageUrl": event.get_cover_image_url(),
            "category": {
                "categoryId": event.get_category().get_category_id(),
                "name": event.get_category().get_name(),
            },
            "organizer": {
                "userId": event.get_organizer().get_user_id(),
                "fullName": event.get_organizer().get_name(),
            },
            "savedCount": saved_count,
            "isSaved": is_saved,
        }

    def _build_domain_student(self, user: User, saved_event_ids: list[int]) -> Student:
        student = Student(
            user_id=user.id,
            name=user.full_name,
            email=user.email,
            password_hash=user.password_hash,
        )
        student._saved_events = saved_event_ids
        return student

    def get_event_detail(self, event_id: int, current_user: User | None = None) -> dict:
        event = self.event_repo.get_by_id(event_id)
        if event is None:
            raise not_found("ไม่พบกิจกรรมที่ต้องการ")

        if event.status != "PUBLISHED":
            if current_user is None or current_user.role not in {"ADMIN", "ORGANIZER"}:
                raise not_found("ไม่พบกิจกรรมที่ต้องการ")

        domain_event = self._to_domain_event(event)
        saved_count = self.event_repo.count_saves(event.id)
        is_saved = False
        if current_user is not None and current_user.role == "STUDENT":
            student = self._build_domain_student(current_user, self.event_repo.get_saved_event_ids(current_user.id))
            is_saved = student.has_saved_event(domain_event)

        return {
            "success": True,
            "message": "ดึงรายละเอียดกิจกรรมสำเร็จ",
            "data": self._to_detail_response(domain_event, saved_count, is_saved, event.cancel_reason),
        }

    def get_my_events(
        self,
        page: int | None,
        page_size: int | None,
        status: str | None,
        search: str | None,
        sort_by: str | None,
        sort_order: str | None,
        current_user: User,
    ) -> dict:
        if current_user.role != "ORGANIZER":
            raise forbidden("เฉพาะ ORGANIZER เท่านั้นที่สามารถดูกิจกรรมของตัวเองได้")

        page_number = self._parse_page(page)
        page_size_number = self._parse_page_size(page_size)
        sort_by_field = self._parse_sort_by(sort_by)
        sort_order_value = self._parse_sort_order(sort_order)

        status_filter = None
        if status is not None:
            normalized = status.strip().upper()
            if normalized not in {"DRAFT", "PUBLISHED", "CANCELLED"}:
                raise bad_request(
                    message="ข้อมูล query ไม่ถูกต้อง",
                    errors=[
                        {
                            "field": "status",
                            "code": "INVALID_STATUS",
                            "detail": "status ต้องเป็น DRAFT, PUBLISHED หรือ CANCELLED",
                        }
                    ],
                )
            status_filter = normalized

        query = self.event_repo.get_query()
        query = query.filter(Event.organizer_id == current_user.id)

        if status_filter is not None:
            query = query.filter(Event.status == status_filter)

        if sort_by_field == "createdAt":
            query = query.order_by(Event.created_at.desc() if sort_order_value == "desc" else Event.created_at.asc())
        else:
            sort_column = Event.start_time if sort_by_field == "startTime" else Event.end_time
            query = query.order_by(sort_column.desc() if sort_order_value == "desc" else sort_column.asc())

        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / page_size_number))
        offset = (page_number - 1) * page_size_number
        orm_events = query.offset(offset).limit(page_size_number).all()

        manager = EventManager()
        for orm_event in orm_events:
            manager.add_event(self._to_domain_event(orm_event))

        filtered_events = manager.get_all_events()
        if search is not None:
            filtered_events = manager.search_by_keyword(search)

        response_events = []
        for event in filtered_events:
            saved_count = self.event_repo.count_saves(event.get_event_id())
            response_events.append({
                "eventId": event.get_event_id(),
                "title": event.get_title(),
                "locationName": event.get_location_name(),
                "status": event.get_status(),
                "savedCount": saved_count,
                "coverImageUrl": event.get_cover_image_url(),
                "startTime": event.get_start_time().isoformat(),
                "endTime": event.get_end_time().isoformat(),
                "category": {
                    "categoryId": event.get_category().get_category_id(),
                    "name": event.get_category().get_name(),
                },
                "organizer": {
                    "userId": event.get_organizer().get_user_id(),
                    "fullName": event.get_organizer().get_name(),
                },
            })

        return {
            "success": True,
            "message": "ดึงรายการกิจกรรมของผู้จัดสำเร็จ",
            "data": response_events,
            "meta": {
                "page": page_number,
                "pageSize": page_size_number,
                "totalItems": total_items,
                "totalPages": total_pages,
            },
        }

    def get_upcoming_events(
        self,
        page: int | None,
        page_size: int | None,
        category_id: int | None,
        sort_by: str | None,
        sort_order: str | None,
    ) -> dict:
        page_number = self._parse_page(page)
        page_size_number = self._parse_page_size(page_size)
        sort_by_field = self._parse_sort_by(sort_by)
        sort_order_value = self._parse_sort_order(sort_order)

        if category_id is not None:
            self._ensure_category_exists(category_id)

        query = self.event_repo.get_query()
        query = query.filter(Event.status == "PUBLISHED")

        now = datetime.now(UTC)
        query = query.filter(Event.start_time > now)

        if category_id is not None:
            query = query.filter(Event.category_id == category_id)

        sort_column = Event.start_time if sort_by_field == "startTime" else Event.end_time
        query = query.order_by(sort_column.desc() if sort_order_value == "desc" else sort_column.asc())

        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / page_size_number))
        offset = (page_number - 1) * page_size_number
        orm_events = query.offset(offset).limit(page_size_number).all()

        response_events = []
        for orm_event in orm_events:
            saved_count = self.event_repo.count_saves(orm_event.id)
            response_events.append({
                "eventId": orm_event.id,
                "title": orm_event.title,
                "locationName": orm_event.location_name,
                "startTime": orm_event.start_time.isoformat(),
                "endTime": orm_event.end_time.isoformat(),
                "status": orm_event.status,
                "coverImageUrl": orm_event.cover_image_url,
                "savedCount": saved_count,
                "category": {
                    "categoryId": orm_event.category.id,
                    "name": orm_event.category.name,
                },
                "organizer": {
                    "userId": orm_event.organizer.id,
                    "fullName": orm_event.organizer.full_name,
                },
            })

        return {
            "success": True,
            "message": "ดึงกิจกรรมที่กำลังจะมาถึงสำเร็จ",
            "data": response_events,
            "meta": {
                "page": page_number,
                "pageSize": page_size_number,
                "totalItems": total_items,
                "totalPages": total_pages,
            },
        }

    def get_active_events(
        self,
        page: int | None,
        page_size: int | None,
        category_id: int | None,
        sort_by: str | None,
        sort_order: str | None,
    ) -> dict:
        page_number = self._parse_page(page)
        page_size_number = self._parse_page_size(page_size)
        sort_by_field = self._parse_sort_by(sort_by)
        sort_order_value = self._parse_sort_order(sort_order)

        if category_id is not None:
            self._ensure_category_exists(category_id)

        query = self.event_repo.get_query()
        query = query.filter(Event.status == "PUBLISHED")

        now = datetime.now(UTC)
        query = query.filter(Event.end_time > now)

        if category_id is not None:
            query = query.filter(Event.category_id == category_id)

        sort_column = Event.start_time if sort_by_field == "startTime" else Event.end_time
        query = query.order_by(sort_column.desc() if sort_order_value == "desc" else sort_column.asc())

        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / page_size_number))
        offset = (page_number - 1) * page_size_number
        orm_events = query.offset(offset).limit(page_size_number).all()

        response_events = []
        for orm_event in orm_events:
            saved_count = self.event_repo.count_saves(orm_event.id)
            response_events.append({
                "eventId": orm_event.id,
                "title": orm_event.title,
                "locationName": orm_event.location_name,
                "status": orm_event.status,
                "startTime": orm_event.start_time.isoformat(),
                "endTime": orm_event.end_time.isoformat(),
                "coverImageUrl": orm_event.cover_image_url,
                "savedCount": saved_count,
                "category": {
                    "categoryId": orm_event.category.id,
                    "name": orm_event.category.name,
                },
                "organizer": {
                    "userId": orm_event.organizer.id,
                    "fullName": orm_event.organizer.full_name,
                },
            })

        return {
            "success": True,
            "message": "ดึงกิจกรรมที่ยัง active สำเร็จ",
            "data": response_events,
            "meta": {
                "page": page_number,
                "pageSize": page_size_number,
                "totalItems": total_items,
                "totalPages": total_pages,
            },
        }

    def create_event(self, payload, current_user: User) -> dict:
        self._ensure_admin_or_organizer(current_user)
        status = self._parse_event_status(payload.status, current_user)
        self._validate_coordinates(payload.latitude, payload.longitude)
        self._ensure_category_exists(payload.category_id)

        if not payload.start_time or not payload.end_time:
            raise bad_request(
                message="ข้อมูลกิจกรรมไม่ครบ",
                errors=[
                    {
                        "field": "startTime/endTime",
                        "code": "MISSING_TIME_RANGE",
                        "detail": "ต้องระบุ startTime และ endTime",
                    }
                ],
            )

        if payload.start_time >= payload.end_time:
            raise bad_request(
                message="ช่วงเวลาของกิจกรรมไม่ถูกต้อง",
                errors=[
                    {
                        "field": "startTime/endTime",
                        "code": "INVALID_TIME_RANGE",
                        "detail": "startTime ต้องน้อยกว่า endTime",
                    }
                ],
            )

        event = self.event_repo.create(
            title=payload.title,
            description=payload.description,
            short_description=payload.short_description,
            location_name=payload.location_name,
            latitude=payload.latitude,
            longitude=payload.longitude,
            start_time=payload.start_time,
            end_time=payload.end_time,
            status=status,
            category_id=payload.category_id,
            organizer_id=current_user.id,
            cover_image_url=payload.cover_image_url,
        )

        return {
            "success": True,
            "message": "สร้างกิจกรรมสำเร็จ",
            "data": {
                "eventId": event.id,
                "title": event.title,
                "status": event.status,
                "categoryId": event.category_id,
                "organizerId": event.organizer_id,
            },
        }

    def _ensure_admin_or_organizer(self, current_user: User) -> None:
        if current_user.role not in {"ADMIN", "ORGANIZER"}:
            raise forbidden("ไม่มีสิทธิ์จัดการกิจกรรม")

    def update_event(self, event_id: int, payload, current_user: User) -> dict:
        event = self.event_repo.get_by_id(event_id)
        if event is None:
            raise not_found("ไม่พบกิจกรรมที่ต้องการ")

        self._ensure_event_owner(event, current_user)

        if payload.title is None and payload.description is None and payload.short_description is None and payload.location_name is None and payload.latitude is None and payload.longitude is None and payload.start_time is None and payload.end_time is None and payload.category_id is None and payload.cover_image_url is None:
            raise bad_request(
                message="ข้อมูลไม่ถูกต้อง",
                errors=[
                    {
                        "field": "body",
                        "code": "EMPTY_UPDATE_PAYLOAD",
                        "detail": "ต้องระบุฟิลด์อย่างน้อย 1 ตัวเพื่อแก้ไขกิจกรรม",
                    }
                ],
            )

        if payload.category_id is not None:
            self._ensure_category_exists(payload.category_id)
            event.category_id = payload.category_id

        if payload.title is not None:
            event.title = payload.title
        if payload.description is not None:
            event.description = payload.description
        if payload.short_description is not None:
            event.short_description = payload.short_description
        if payload.cover_image_url is not None:
            event.cover_image_url = payload.cover_image_url
        if payload.location_name is not None:
            event.location_name = payload.location_name
        if payload.latitude is not None:
            event.latitude = payload.latitude
        if payload.longitude is not None:
            event.longitude = payload.longitude
        if payload.start_time is not None:
            event.start_time = payload.start_time
        if payload.end_time is not None:
            event.end_time = payload.end_time

        if event.latitude is not None and event.longitude is not None:
            self._validate_coordinates(event.latitude, event.longitude)

        if event.start_time is not None and event.end_time is not None and event.start_time >= event.end_time:
            raise bad_request(
                message="ช่วงเวลาของกิจกรรมไม่ถูกต้อง",
                errors=[
                    {
                        "field": "startTime/endTime",
                        "code": "INVALID_TIME_RANGE",
                        "detail": "startTime ต้องน้อยกว่า endTime",
                    }
                ],
            )

        updated_event = self.event_repo.save(event)

        return {
            "success": True,
            "message": "แก้ไขกิจกรรมสำเร็จ",
            "data": {
                "eventId": updated_event.id,
                "title": updated_event.title,
                "locationName": updated_event.location_name,
                "status": updated_event.status,
            },
        }

    def delete_event(self, event_id: int, current_user: User) -> dict:
        event = self.event_repo.get_by_id(event_id)
        if event is None:
            raise not_found("ไม่พบกิจกรรมที่ต้องการ")

        self._ensure_event_owner(event, current_user)
        self.event_repo.delete(event)

        return {
            "success": True,
            "message": "ลบกิจกรรมสำเร็จ",
            "data": {
                "eventId": event_id,
                "deleted": True,
            },
        }

    def publish_event(self, event_id: int, current_user: User) -> dict:
        self._ensure_admin(current_user)

        event = self.event_repo.get_by_id(event_id)
        if event is None:
            raise not_found("ไม่พบกิจกรรมที่ต้องการ")

        if event.status == "PUBLISHED":
            raise conflict(
                message="สถานะกิจกรรมไม่ถูกต้อง",
                errors=[
                    {
                        "field": "status",
                        "code": "ALREADY_PUBLISHED",
                        "detail": "กิจกรรมเผยแพร่แล้ว",
                    }
                ],
            )

        if event.status == "CANCELLED":
            raise conflict(
                message="ไม่สามารถเผยแพร่กิจกรรมที่ถูกยกเลิกแล้ว",
                errors=[
                    {
                        "field": "status",
                        "code": "INVALID_STATE_TRANSITION",
                        "detail": "กิจกรรมที่ถูกยกเลิกไม่สามารถเผยแพร่ได้",
                    }
                ],
            )

        self._ensure_publishable(event)
        event.status = "PUBLISHED"
        updated_event = self.event_repo.save(event)

        return {
            "success": True,
            "message": "เผยแพร่กิจกรรมสำเร็จ",
            "data": {
                "eventId": updated_event.id,
                "status": updated_event.status,
            },
        }

    def cancel_event(self, event_id: int, payload, current_user: User) -> dict:
        event = self.event_repo.get_by_id(event_id)
        if event is None:
            raise not_found("ไม่พบกิจกรรมที่ต้องการ")

        if current_user.role == "ORGANIZER":
            self._ensure_event_owner(event, current_user)
        elif current_user.role != "ADMIN":
            raise forbidden("ไม่มีสิทธิ์ยกเลิกกิจกรรมนี้")

        if not payload.reason.strip():
            raise bad_request(
                message="ข้อมูลไม่ถูกต้อง",
                errors=[
                    {
                        "field": "reason",
                        "code": "INVALID_REASON",
                        "detail": "reason ต้องไม่ว่าง",
                    }
                ],
            )

        if event.status == "CANCELLED":
            raise conflict(
                message="สถานะกิจกรรมไม่ถูกต้อง",
                errors=[
                    {
                        "field": "status",
                        "code": "ALREADY_CANCELLED",
                        "detail": "กิจกรรมถูกยกเลิกแล้ว",
                    }
                ],
            )

        event.status = "CANCELLED"
        event.cancel_reason = payload.reason
        updated_event = self.event_repo.save(event)

        return {
            "success": True,
            "message": "ยกเลิกกิจกรรมสำเร็จ",
            "data": {
                "eventId": updated_event.id,
                "status": updated_event.status,
                "reason": updated_event.cancel_reason,
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

    def get_nearby_events(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        search: str | None,
        category_id: int | None,
        page: int | None,
        page_size: int | None,
        sort_by: str | None,
        sort_order: str | None,
    ) -> dict:
        location_service = LocationService()
        
        if not location_service.validate_coordinates(latitude, longitude):
            raise bad_request(
                message="ข้อมูลพิกัดไม่ถูกต้อง",
                errors=[
                    {
                        "field": "latitude/longitude",
                        "code": "INVALID_COORDINATES",
                        "detail": "latitude ต้องอยู่ระหว่าง -90 ถึง 90 และ longitude ต้องอยู่ระหว่าง -180 ถึง 180",
                    }
                ],
            )
        
        if radius_km <= 0 or radius_km > 100:
            raise bad_request(
                message="ข้อมูลรัศมีไม่ถูกต้อง",
                errors=[
                    {
                        "field": "radiusKm",
                        "code": "INVALID_RADIUS",
                        "detail": "radiusKm ต้องมากกว่า 0 และไม่เกิน 100 กิโลเมตร",
                    }
                ],
            )
        
        if category_id is not None:
            self._ensure_category_exists(category_id)
        
        page_number = self._parse_page(page)
        page_size_number = self._parse_page_size(page_size)
        sort_by_field = self._parse_sort_by_nearby(sort_by)
        sort_order_value = self._parse_sort_order(sort_order)
        
        query = self.event_repo.get_query()
        query = query.filter(Event.status == "PUBLISHED")
        
        if search is not None:
            query = query.filter(Event.title.ilike(f"%{search}%"))
        
        if category_id is not None:
            query = query.filter(Event.category_id == category_id)
        
        orm_events = query.all()
        
        # Filter by distance
        nearby_events = []
        for orm_event in orm_events:
            distance = location_service.calculate_distance(latitude, longitude, orm_event.latitude, orm_event.longitude)
            if location_service.is_within_radius(distance, radius_km):
                nearby_events.append((orm_event, distance))
        
        # Sort
        if sort_by_field == "distance":
            nearby_events.sort(key=lambda x: x[1], reverse=sort_order_value == "desc")
        else:
            # Default sort by startTime
            nearby_events.sort(key=lambda x: x[0].start_time, reverse=sort_order_value == "desc")
        
        # Paginate
        total_items = len(nearby_events)
        total_pages = max(1, math.ceil(total_items / page_size_number))
        start_index = (page_number - 1) * page_size_number
        end_index = start_index + page_size_number
        paged_events = nearby_events[start_index:end_index]
        
        # Build response
        response_events = []
        category_repo = CategoryRepository(self.db)
        for orm_event, distance in paged_events:
            category = category_repo.get_by_id(orm_event.category_id)
            response_events.append({
                "eventId": orm_event.id,
                "title": orm_event.title,
                "locationName": orm_event.location_name,
                "latitude": orm_event.latitude,
                "longitude": orm_event.longitude,
                "distanceKm": round(distance, 2),
                "startTime": orm_event.start_time.isoformat(),
                "endTime": orm_event.end_time.isoformat(),
                "status": orm_event.status,
                "coverImageUrl": orm_event.cover_image_url,
                "category": {
                    "categoryId": category.id,
                    "name": category.name,
                },
                "organizer": {
                    "userId": orm_event.organizer.id,
                    "fullName": orm_event.organizer.full_name,
                },
            })
        
        return {
            "success": True,
            "message": "ดึงกิจกรรมใกล้ตัวสำเร็จ",
            "data": response_events,
            "meta": {
                "page": page_number,
                "pageSize": page_size_number,
                "totalItems": total_items,
                "totalPages": total_pages,
            },
        }

    def get_map_events(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        category_id: int | None,
        search: str | None,
    ) -> dict:
        location_service = LocationService()
        
        if not location_service.validate_coordinates(latitude, longitude):
            raise bad_request(
                message="ข้อมูลพิกัดไม่ถูกต้อง",
                errors=[
                    {
                        "field": "latitude/longitude",
                        "code": "INVALID_COORDINATES",
                        "detail": "latitude ต้องอยู่ระหว่าง -90 ถึง 90 และ longitude ต้องอยู่ระหว่าง -180 ถึง 180",
                    }
                ],
            )
        
        if radius_km <= 0 or radius_km > 100:
            raise bad_request(
                message="ข้อมูลรัศมีไม่ถูกต้อง",
                errors=[
                    {
                        "field": "radiusKm",
                        "code": "INVALID_RADIUS",
                        "detail": "radiusKm ต้องมากกว่า 0 และไม่เกิน 100 กิโลเมตร",
                    }
                ],
            )
        
        if category_id is not None:
            self._ensure_category_exists(category_id)
        
        query = self.event_repo.get_query()
        query = query.filter(Event.status == "PUBLISHED")
        
        if search is not None:
            query = query.filter(Event.title.ilike(f"%{search}%"))
        
        if category_id is not None:
            query = query.filter(Event.category_id == category_id)
        
        orm_events = query.all()
        
        # Filter by distance
        nearby_events = []
        for orm_event in orm_events:
            distance = location_service.calculate_distance(latitude, longitude, orm_event.latitude, orm_event.longitude)
            if location_service.is_within_radius(distance, radius_km):
                nearby_events.append((orm_event, distance))
        
        # Sort by distance ascending (default for map)
        nearby_events.sort(key=lambda x: x[1])
        
        # Build response (no pagination)
        response_events = []
        for orm_event, distance in nearby_events:
            response_events.append({
                "eventId": orm_event.id,
                "title": orm_event.title,
                "latitude": orm_event.latitude,
                "longitude": orm_event.longitude,
                "locationName": orm_event.location_name,
                "distanceKm": round(distance, 2),
                "startTime": orm_event.start_time.isoformat(),
                "endTime": orm_event.end_time.isoformat(),
                "status": orm_event.status,
                "coverImageUrl": orm_event.cover_image_url,
                "category": {
                    "categoryId": orm_event.category.id,
                    "name": orm_event.category.name,
                },
            })
        
        return {
            "success": True,
            "message": "ดึงข้อมูลแผนที่สำเร็จ",
            "data": response_events,
        }

    def _parse_sort_by_nearby(self, sort_by: str | None) -> str:
        if sort_by is None:
            return "startTime"
        allowed = {"startTime", "endTime", "distance"}
        if sort_by not in allowed:
            raise bad_request(
                message="ข้อมูล query ไม่ถูกต้อง",
                errors=[
                    {
                        "field": "sortBy",
                        "code": "INVALID_SORT_BY",
                        "detail": f"sortBy ต้องเป็นหนึ่งใน {', '.join(allowed)}",
                    }
                ],
            )
        return sort_by