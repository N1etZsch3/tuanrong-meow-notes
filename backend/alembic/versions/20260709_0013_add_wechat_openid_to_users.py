"""add wechat openid binding fields to users

Revision ID: 20260709_0013
Revises: 20260706_0012
Create Date: 2026-07-09
"""

import sqlalchemy as sa

from alembic import op

revision = "20260709_0013"
down_revision = "20260706_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("wechat_openid", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("wechat_bound_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users",
        sa.Column("last_wechat_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "uq_users_wechat_openid",
        "users",
        ["wechat_openid"],
        unique=True,
        postgresql_where=sa.text("wechat_openid IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_users_wechat_openid", table_name="users")
    op.drop_column("users", "last_wechat_login_at")
    op.drop_column("users", "wechat_bound_at")
    op.drop_column("users", "wechat_openid")
