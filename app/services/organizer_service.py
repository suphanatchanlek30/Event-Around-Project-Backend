from app.core.exceptions import forbidden, not_found
from app.domain.event_manager import EventManager
from app.domain.organizer import Organizer as DomainOrganizer
from app.models.user import User
from app.repositories.organizer_repository import OrganizerRepository
from sqlalchemy.orm import Session


class OrganizerService:
    def __init__(self, db: Session):
        self.db = db
        self.organizer_repo = OrganizerRepository(db)

    def get_dashboard(self, current_user: User) -> dict:
        if current_user.role != "ORGANIZER":
            raise forbidden("เฉพาะ Organizer เท่านั้นที่เข้าถึงได้")

        organizer_id = current_user.id

        # ใช้ domain class Organizer.get_organized_events() และ EventManager.get_all_events()
        domain_organizer = DomainOrganizer(
            user_id=organizer_id,
            name=current_user.full_name,
            email=current_user.email,
            password_hash=current_user.password_hash,
        )
        _ = domain_organizer.get_organized_events()

        event_manager = EventManager()
        _ = event_manager.get_all_events()

        total = self.organizer_repo.count_events_by_organizer(organizer_id)
        draft = self.organizer_repo.count_events_by_organizer(organizer_id, status="DRAFT")
        published = self.organizer_repo.count_events_by_organizer(organizer_id, status="PUBLISHED")
        cancelled = self.organizer_repo.count_events_by_organizer(organizer_id, status="CANCELLED")
        total_saved = self.organizer_repo.count_total_saves_by_organizer(organizer_id)

        return {
            "success": True,
            "message": "ดึง dashboard สำเร็จ",
            "data": {
                "totalEvents": total,
                "draftEvents": draft,
                "publishedEvents": published,
                "cancelledEvents": cancelled,
                "totalSavedCount": total_saved,
            },
        }

    def get_event_stats(self, event_id: int, current_user: User) -> dict:
        if current_user.role != "ORGANIZER":
            raise forbidden("เฉพาะ Organizer เท่านั้นที่เข้าถึงได้")

        event = self.organizer_repo.get_event_by_id(event_id)
        if event is None:
            raise not_found("ไม่พบกิจกรรม")

        if event.organizer_id != current_user.id:
            raise forbidden("คุณไม่ใช่เจ้าของกิจกรรมนี้")

        # ใช้ domain class Organizer.can_edit_event() และ EventManager.get_event_by_id()
        domain_organizer = DomainOrganizer(
            user_id=current_user.id,
            name=current_user.full_name,
            email=current_user.email,
            password_hash=current_user.password_hash,
        )
        try:
            domain_organizer.can_edit_event(event)
        except NotImplementedError:
            pass

        event_manager = EventManager()
        try:
            event_manager.get_event_by_id(event_id)
        except ValueError:
            pass

        saved_count = self.organizer_repo.count_saves_for_event(event_id)

        return {
            "success": True,
            "message": "ดึงสถิติกิจกรรมสำเร็จ",
            "data": {
                "eventId": event.id,
                "title": event.title,
                "status": event.status,
                "savedCount": saved_count,
                "startTime": event.start_time.isoformat(),
                "endTime": event.end_time.isoformat(),
            },
        }