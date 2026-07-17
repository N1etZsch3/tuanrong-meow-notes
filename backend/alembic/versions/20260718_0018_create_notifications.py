"""create notifications and user notification settings tables

Revision ID: 20260718_0018
Revises: 20260717_0017
Create Date: 2026-07-18
"""

import sqlalchemy as sa

from alembic import op

revision = "20260718_0018"
down_revision = "20260717_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("notification_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("related_type", sa.String(length=64), nullable=True),
        sa.Column("related_id", sa.Uuid(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_notifications_user_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index(
        "idx_notifications_type", "notifications", ["notification_type"]
    )
    op.create_index(
        "idx_notifications_user_read", "notifications", ["user_id", "is_read"]
    )
    op.create_index(
        "idx_notifications_user_created", "notifications", ["user_id", "created_at"]
    )

    op.create_table(
        "user_notification_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("task_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "feeding_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "medicine_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "supply_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "member_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("cat_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "announcement_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_user_notification_settings_user_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_user_notification_settings_user_id",
        "user_notification_settings",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_user_notification_settings_user_id", table_name="user_notification_settings"
    )
    op.drop_table("user_notification_settings")
    op.drop_index("idx_notifications_user_created", table_name="notifications")
    op.drop_index("idx_notifications_user_read", table_name="notifications")
    op.drop_index("idx_notifications_type", table_name="notifications")
    op.drop_index("idx_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
