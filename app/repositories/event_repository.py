from datetime import datetime

from app.models.event import Event
from app.models.event_save import EventSave
from sqlalchemy import func
from sqlalchemy.orm import Session


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

    def create(
        self,
        title: str,
        description: str | None,
        short_description: str | None,
        location_name: str,
        latitude: float,
        longitude: float,
        start_time: datetime,
        end_time: datetime,
        status: str,
        category_id: int,
        organizer_id: int,
        cover_image_url: str | None = None,
        cancel_reason: str | None = None,
    ) -> Event:
        event = Event(
            title=title,
            description=description,
            short_description=short_description,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            start_time=start_time,
            end_time=end_time,
            status=status,
            category_id=category_id,
            organizer_id=organizer_id,
            cover_image_url=cover_image_url,
            cancel_reason=cancel_reason,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def save(self, event: Event) -> Event:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def delete(self, event: Event) -> None:
        self.db.delete(event)
        self.db.commit()

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