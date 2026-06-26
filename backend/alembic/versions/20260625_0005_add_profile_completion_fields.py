"""add profile completion fields

Revision ID: 20260625_0005
Revises: 20260624_0004
Create Date: 2026-06-25
"""

import sqlalchemy as sa

from alembic import op

revision = "20260625_0005"
down_revision = "20260624_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column(
            "profile_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column("profile_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_user_profiles_department", "user_profiles", ["department"])
    op.create_index("idx_user_profiles_completed", "user_profiles", ["profile_completed"])


def downgrade() -> None:
    op.drop_index("idx_user_profiles_completed", table_name="user_profiles")
    op.drop_index("idx_user_profiles_department", table_name="user_profiles")
    op.drop_column("user_profiles", "profile_completed_at")
    op.drop_column("user_profiles", "profile_completed")
