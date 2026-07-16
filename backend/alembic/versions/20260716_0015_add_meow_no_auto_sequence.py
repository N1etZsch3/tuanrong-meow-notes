"""add independent meow number auto sequence

Revision ID: 20260716_0015
Revises: 20260712_0014
Create Date: 2026-07-16
"""

from alembic import op

revision = "20260716_0015"
down_revision = "20260712_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "CREATE SEQUENCE IF NOT EXISTS meow_no_auto_sequence "
            "START WITH 1 INCREMENT BY 1 MINVALUE 1 NO MAXVALUE CACHE 1"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP SEQUENCE IF EXISTS meow_no_auto_sequence")
