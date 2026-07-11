"""add file content security review state

Revision ID: 20260712_0014
Revises: 20260709_0013
Create Date: 2026-07-12
"""

import sqlalchemy as sa

from alembic import op

revision = "20260712_0014"
down_revision = "20260709_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "file_assets",
        sa.Column("security_status", sa.String(length=32), nullable=False, server_default="legacy"),
    )
    op.add_column("file_assets", sa.Column("security_provider", sa.String(length=32)))
    op.add_column("file_assets", sa.Column("security_trace_id", sa.String(length=128)))
    op.add_column("file_assets", sa.Column("security_suggest", sa.String(length=32)))
    op.add_column("file_assets", sa.Column("security_label", sa.Integer()))
    op.add_column("file_assets", sa.Column("security_error_code", sa.Integer()))
    op.add_column(
        "file_assets",
        sa.Column("security_submitted_at", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "file_assets",
        sa.Column("security_checked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_file_assets_security_status", "file_assets", ["security_status"])
    op.create_index(
        "uq_file_assets_security_trace_id",
        "file_assets",
        ["security_trace_id"],
        unique=True,
        postgresql_where=sa.text("security_trace_id IS NOT NULL"),
    )
    op.alter_column("file_assets", "security_status", server_default="pending")

    op.add_column(
        "user_profiles",
        sa.Column("avatar_review_asset_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "user_profiles",
        sa.Column("avatar_review_status", sa.String(length=32), nullable=False, server_default="idle"),
    )
    op.add_column(
        "user_profiles",
        sa.Column("avatar_review_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_user_profiles_avatar_review_asset_id",
        "user_profiles",
        "file_assets",
        ["avatar_review_asset_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_user_profiles_avatar_review_asset_id",
        "user_profiles",
        type_="foreignkey",
    )
    op.drop_column("user_profiles", "avatar_review_updated_at")
    op.drop_column("user_profiles", "avatar_review_status")
    op.drop_column("user_profiles", "avatar_review_asset_id")

    op.drop_index("uq_file_assets_security_trace_id", table_name="file_assets")
    op.drop_index("idx_file_assets_security_status", table_name="file_assets")
    op.drop_column("file_assets", "security_checked_at")
    op.drop_column("file_assets", "security_submitted_at")
    op.drop_column("file_assets", "security_error_code")
    op.drop_column("file_assets", "security_label")
    op.drop_column("file_assets", "security_suggest")
    op.drop_column("file_assets", "security_trace_id")
    op.drop_column("file_assets", "security_provider")
    op.drop_column("file_assets", "security_status")
