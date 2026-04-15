from datetime import datetime

from app.core.database import Base
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class EventSave(Base):
    __tablename__ = "event_saves"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    event = relationship("Event", lazy="joined")
    user = relationship("User", lazy="joined")
