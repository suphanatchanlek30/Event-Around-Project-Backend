"""create event categories table

Revision ID: 0003_event_categories
Revises: 0002_auth_tokens
Create Date: 2026-04-10 21:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_event_categories"
down_revision: Union[str, Sequence[str], None] = "0002_auth_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_categories",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("ix_event_categories_id", "event_categories", ["id"], unique=False)
    op.create_index("ix_event_categories_name", "event_categories", ["name"], unique=True)
    op.create_index("ix_event_categories_is_active", "event_categories", ["is_active"], unique=False)

    op.alter_column("event_categories", "is_active", server_default=None)
    op.alter_column("event_categories", "created_at", server_default=None)
    op.alter_column("event_categories", "updated_at", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_event_categories_is_active", table_name="event_categories")
    op.drop_index("ix_event_categories_name", table_name="event_categories")
    op.drop_index("ix_event_categories_id", table_name="event_categories")
    op.drop_table("event_categories")
