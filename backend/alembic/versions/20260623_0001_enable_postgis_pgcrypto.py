"""enable postgis and pgcrypto extensions

Revision ID: 20260623_0001
Revises:
Create Date: 2026-06-23
"""

from alembic import op

revision = "20260623_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")


def downgrade() -> None:
    pass
