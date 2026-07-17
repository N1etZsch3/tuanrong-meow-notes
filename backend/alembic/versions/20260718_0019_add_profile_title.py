"""add unique user profile title

Revision ID: 20260718_0019
Revises: 20260718_0018
Create Date: 2026-07-18
"""

import sqlalchemy as sa

from alembic import op

revision = "20260718_0019"
down_revision = "20260718_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("title", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "uq_user_profiles_title",
        "user_profiles",
        ["title"],
        unique=True,
        sqlite_where=sa.text("title IS NOT NULL"),
        postgresql_where=sa.text("title IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_user_profiles_title", table_name="user_profiles")
    op.drop_column("user_profiles", "title")
