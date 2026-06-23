"""create auth tables

Revision ID: 20260623_0002
Revises: 20260623_0001
Create Date: 2026-06-23
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260623_0002"
down_revision = "20260623_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("student_no", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="member"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("password_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("login_failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_no", name="uq_users_student_no"),
    )
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_users_status", "users", ["status"])
    op.create_index(
        "idx_users_locked_until",
        "users",
        ["locked_until"],
        postgresql_where=sa.text("locked_until IS NOT NULL"),
    )

    op.create_table(
        "auth_captchas",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("scene", sa.String(length=32), nullable=False, server_default="login"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_auth_captchas_expires_at", "auth_captchas", ["expires_at"])
    op.create_index("idx_auth_captchas_scene_created", "auth_captchas", ["scene", sa.text("created_at DESC")])
    op.create_index(
        "idx_auth_captchas_unused",
        "auth_captchas",
        ["scene", "expires_at"],
        postgresql_where=sa.text("used_at IS NULL"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nickname", sa.String(length=64), nullable=False),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("real_name", sa.String(length=64), nullable=True),
        sa.Column("department", sa.String(length=128), nullable=True),
        sa.Column("grade", sa.String(length=32), nullable=True),
        sa.Column("joined_at", sa.Date(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("contact_info", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_profiles_user"),
    )

    op.create_table(
        "admin_operation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("admin_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_type", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("before_data", postgresql.JSONB(), nullable=True),
        sa.Column("after_data", postgresql.JSONB(), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("admin_operation_logs")
    op.drop_table("user_profiles")
    op.drop_index("idx_auth_captchas_unused", table_name="auth_captchas")
    op.drop_index("idx_auth_captchas_scene_created", table_name="auth_captchas")
    op.drop_index("idx_auth_captchas_expires_at", table_name="auth_captchas")
    op.drop_table("auth_captchas")
    op.drop_index("idx_users_locked_until", table_name="users")
    op.drop_index("idx_users_status", table_name="users")
    op.drop_index("idx_users_role", table_name="users")
    op.drop_table("users")
