from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_save import EventSave


class OrganizerRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_events_by_organizer(self, organizer_id: int, status: str | None = None) -> int:
        query = self.db.query(func.count(Event.id)).filter(Event.organizer_id == organizer_id)
        if status is not None:
            query = query.filter(Event.status == status)
        return query.scalar() or 0

    def count_total_saves_by_organizer(self, organizer_id: int) -> int:
        return (
            self.db.query(func.count(EventSave.id))
            .join(Event, EventSave.event_id == Event.id)
            .filter(Event.organizer_id == organizer_id)
            .scalar() or 0
        )