"""create event import logs

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-13 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007"
down_revision: Union[str, Sequence[str], None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_import_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organizer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("total_records", sa.Integer(), nullable=False, default=0),
        sa.Column("success_records", sa.Integer(), nullable=False, default=0),
        sa.Column("failed_records", sa.Integer(), nullable=False, default=0),
        sa.Column("default_status", sa.String(length=50), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("event_import_logs")
