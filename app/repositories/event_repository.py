from datetime import datetime

from sqlalchemy.orm import Session

from app.models.event import Event


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
