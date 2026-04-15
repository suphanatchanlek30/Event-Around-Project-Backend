from app.models.event_save import EventSave
from sqlalchemy import func
from sqlalchemy.orm import Session


class SavedEventRepository:
    def __init__(self, db: Session):
        self.db = db

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

    def get_saved_events_query(self, user_id: int):
        return (
            self.db.query(EventSave)
            .filter(EventSave.user_id == user_id)
            .join(EventSave.event)
        )

    def get_saved_event(self, event_id: int, user_id: int) -> EventSave | None:
        return self.db.query(EventSave).filter(
            EventSave.event_id == event_id,
            EventSave.user_id == user_id,
        ).first()

    def create_saved_event(self, event_id: int, user_id: int) -> EventSave:
        event_save = EventSave(event_id=event_id, user_id=user_id)
        self.db.add(event_save)
        self.db.commit()
        self.db.refresh(event_save)
        return event_save

    def delete_saved_event(self, event_save: EventSave) -> None:
        self.db.delete(event_save)
        self.db.commit()
