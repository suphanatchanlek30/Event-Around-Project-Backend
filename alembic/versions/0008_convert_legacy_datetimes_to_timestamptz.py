"""convert legacy naive datetimes to timestamptz

Revision ID: 0008_convert_legacy_datetimes
Revises: 0007
Create Date: 2026-04-30 10:30:00
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0008_convert_legacy_datetimes"
down_revision: Union[str, Sequence[str], None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LEGACY_NAIVE_COLUMNS: dict[str, tuple[str, ...]] = {
    "users": ("created_at", "updated_at"),
    "refresh_tokens": ("expires_at", "revoked_at", "created_at"),
    "event_categories": ("created_at", "updated_at"),
    "events": ("created_at", "updated_at"),
    "event_saves": ("created_at",),
}


def _convert_columns(sql_type: str, using_timezone: str) -> None:
    for table_name, columns in LEGACY_NAIVE_COLUMNS.items():
        for column_name in columns:
            op.execute(
                f"ALTER TABLE {table_name} "
                f"ALTER COLUMN {column_name} TYPE {sql_type} "
                f"USING {column_name} AT TIME ZONE '{using_timezone}'"
            )


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    _convert_columns("TIMESTAMP WITH TIME ZONE", "UTC")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    _convert_columns("TIMESTAMP WITHOUT TIME ZONE", "UTC")