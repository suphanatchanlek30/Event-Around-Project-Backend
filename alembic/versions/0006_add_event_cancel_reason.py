"""add cancel reason to events

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-11 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("events", sa.Column("cancel_reason", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "cancel_reason")
