from datetime import datetime

from app.core.database import Base
from app.core.timezone import UTCDateTime, get_now_utc
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column


class EventCategory(Base):
    __tablename__ = "event_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=get_now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        default=get_now_utc,
        onupdate=get_now_utc,
        nullable=False,
    )
