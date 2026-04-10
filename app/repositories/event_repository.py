from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_save import EventSave


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_query(self):
        return self.db.query(Event)

    def list_events(
        self,
        status: str | None = None,
        start_from: datetime | None = None,
        end_to: datetime | None = None,
    ):
        query = self.get_query()

        if status is not None:
            query = query.filter(Event.status == status)

        if start_from is not None:
            query = query.filter(Event.start_time >= start_from)

        if end_to is not None:
            query = query.filter(Event.end_time <= end_to)

        return query.order_by(Event.start_time.asc())

    def get_by_id(self, event_id: int) -> Event | None:
        return self.get_query().filter(Event.id == event_id).first()

    def count_saves(self, event_id: int) -> int:
        return self.db.query(func.count(EventSave.id)).filter(EventSave.event_id == event_id).scalar() or 0

    def is_saved_by_user(self, event_id: int, user_id: int) -> bool:
        return self.db.query(EventSave).filter(
            EventSave.event_id == event_id,
            EventSave.user_id == user_id,
        ).first() is not None

    def get_saved_event_ids(self, user_id: int) -> list[int]:
        rows = self.db.query(EventSave.event_id).filter(EventSave.user_id == user_id).all()
        return [row[0] for row in rows]
