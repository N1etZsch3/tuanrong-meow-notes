"""create file asset tables

Revision ID: 20260627_0007
Revises: 20260625_0006
Create Date: 2026-06-27
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260627_0007"
down_revision = "20260625_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "file_assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("storage_provider", sa.String(length=32), nullable=False, server_default="tencent_cos"),
        sa.Column("bucket", sa.String(length=128), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=False),
        sa.Column("env", sa.String(length=32), nullable=False, server_default="dev"),
        sa.Column("usage_type", sa.String(length=64), nullable=False),
        sa.Column("owner_type", sa.String(length=64), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_filename", sa.String(length=255), nullable=True),
        sa.Column("source_mime_type", sa.String(length=64), nullable=True),
        sa.Column("source_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("source_width", sa.Integer(), nullable=True),
        sa.Column("source_height", sa.Integer(), nullable=True),
        sa.Column("source_checksum_sha256", sa.String(length=128), nullable=True),
        sa.Column("default_variant_key", sa.String(length=64), nullable=False, server_default="display"),
        sa.Column("default_url", sa.String(length=1024), nullable=True),
        sa.Column("default_thumb_variant_key", sa.String(length=64), nullable=False, server_default="thumb_md"),
        sa.Column("default_thumb_url", sa.String(length=1024), nullable=True),
        sa.Column("process_preset", sa.String(length=64), nullable=False),
        sa.Column("process_status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="internal"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_file_assets_owner_type", "file_assets", ["owner_type"])
    op.create_index("idx_file_assets_owner_id", "file_assets", ["owner_id"])
    op.create_index("idx_file_assets_usage_type", "file_assets", ["usage_type"])
    op.create_index("idx_file_assets_uploaded_by", "file_assets", ["uploaded_by"])
    op.create_index("idx_file_assets_status", "file_assets", ["process_status"])
    op.create_index("idx_file_assets_deleted_at", "file_assets", ["deleted_at"])
    op.create_index("idx_file_assets_source_checksum", "file_assets", ["source_checksum_sha256"])

    op.create_table(
        "file_asset_variants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("file_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_key", sa.String(length=64), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False, server_default="image/jpeg"),
        sa.Column("file_ext", sa.String(length=16), nullable=False, server_default="jpg"),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("quality", sa.Integer(), nullable=True),
        sa.Column("resize_mode", sa.String(length=32), nullable=False, server_default="fit"),
        sa.Column("checksum_sha256", sa.String(length=128), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["file_asset_id"], ["file_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_asset_id", "variant_key", name="uq_file_asset_variants_asset_key"),
    )
    op.create_index("idx_file_asset_variants_asset", "file_asset_variants", ["file_asset_id"])
    op.create_index("idx_file_asset_variants_key", "file_asset_variants", ["variant_key"])
    op.create_index("idx_file_asset_variants_deleted_at", "file_asset_variants", ["deleted_at"])
    op.create_index(
        "uq_file_asset_variants_object_key",
        "file_asset_variants",
        ["object_key"],
        unique=True,
    )

    op.add_column(
        "user_profiles",
        sa.Column("avatar_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("user_profiles", sa.Column("avatar_thumb_url", sa.String(length=1024), nullable=True))
    op.create_foreign_key(
        "fk_user_profiles_avatar_asset_id",
        "user_profiles",
        "file_assets",
        ["avatar_asset_id"],
        ["id"],
    )
    op.create_index(
        "idx_user_profiles_avatar_asset",
        "user_profiles",
        ["avatar_asset_id"],
        postgresql_where=sa.text("avatar_asset_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_user_profiles_avatar_asset", table_name="user_profiles")
    op.drop_constraint("fk_user_profiles_avatar_asset_id", "user_profiles", type_="foreignkey")
    op.drop_column("user_profiles", "avatar_thumb_url")
    op.drop_column("user_profiles", "avatar_asset_id")

    op.drop_index("uq_file_asset_variants_object_key", table_name="file_asset_variants")
    op.drop_index("idx_file_asset_variants_deleted_at", table_name="file_asset_variants")
    op.drop_index("idx_file_asset_variants_key", table_name="file_asset_variants")
    op.drop_index("idx_file_asset_variants_asset", table_name="file_asset_variants")
    op.drop_table("file_asset_variants")

    op.drop_index("idx_file_assets_source_checksum", table_name="file_assets")
    op.drop_index("idx_file_assets_deleted_at", table_name="file_assets")
    op.drop_index("idx_file_assets_status", table_name="file_assets")
    op.drop_index("idx_file_assets_uploaded_by", table_name="file_assets")
    op.drop_index("idx_file_assets_usage_type", table_name="file_assets")
    op.drop_index("idx_file_assets_owner_id", table_name="file_assets")
    op.drop_index("idx_file_assets_owner_type", table_name="file_assets")
    op.drop_table("file_assets")
