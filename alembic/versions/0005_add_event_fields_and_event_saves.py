"""add event detail fields and event saves

Revision ID: 0005
Revises: 0004_create_events
Create Date: 2026-04-11 00:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004_create_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("events", sa.Column("short_description", sa.String(length=500), nullable=True))
    op.add_column("events", sa.Column("cover_image_url", sa.String(length=500), nullable=True))

    op.create_table(
        "event_saves",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_event_saves_event_id", "event_saves", ["event_id"], unique=False)
    op.create_index("ix_event_saves_user_id", "event_saves", ["user_id"], unique=False)
    op.create_index("ix_event_saves_event_user", "event_saves", ["event_id", "user_id"], unique=True)

    op.alter_column("event_saves", "created_at", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_event_saves_event_user", table_name="event_saves")
    op.drop_index("ix_event_saves_user_id", table_name="event_saves")
    op.drop_index("ix_event_saves_event_id", table_name="event_saves")
    op.drop_table("event_saves")
    op.drop_column("events", "cover_image_url")
    op.drop_column("events", "short_description")
