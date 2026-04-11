"""create events table

Revision ID: 0004_create_events
Revises: 0003_event_categories
Create Date: 2026-04-11 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_create_events"
down_revision: Union[str, Sequence[str], None] = "0003_event_categories"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("location_name", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'DRAFT'")),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("event_categories.id"), nullable=False),
        sa.Column("organizer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_events_id", "events", ["id"], unique=False)
    op.create_index("ix_events_status", "events", ["status"], unique=False)
    op.create_index("ix_events_category_id", "events", ["category_id"], unique=False)
    op.create_index("ix_events_organizer_id", "events", ["organizer_id"], unique=False)

    op.alter_column("events", "status", server_default=None)
    op.alter_column("events", "created_at", server_default=None)
    op.alter_column("events", "updated_at", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_events_organizer_id", table_name="events")
    op.drop_index("ix_events_category_id", table_name="events")
    op.drop_index("ix_events_status", table_name="events")
    op.drop_index("ix_events_id", table_name="events")
    op.drop_table("events")
