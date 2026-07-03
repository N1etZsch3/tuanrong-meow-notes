"""create supply point tables

Revision ID: 20260703_0011
Revises: 20260630_0010
Create Date: 2026-07-03
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260703_0011"
down_revision = "20260630_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE map_marker_configs
        SET business_type = 'supply'
        WHERE marker_key = 'supply_food'
        """
    )

    op.create_table(
        "supply_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("map_point_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("usage_instruction", sa.Text(), nullable=True),
        sa.Column("access_instruction", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["map_point_id"], ["map_points.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("map_point_id", name="uq_supply_points_map_point"),
    )
    op.create_index("idx_supply_points_name", "supply_points", ["name"])
    op.create_index("idx_supply_points_map_point", "supply_points", ["map_point_id"])
    op.create_index("idx_supply_points_status_public", "supply_points", ["status", "is_public"])
    op.create_index("idx_supply_points_created_by", "supply_points", ["created_by"])
    op.create_index("idx_supply_points_updated_by", "supply_points", ["updated_by"])
    op.create_index("idx_supply_points_deleted_at", "supply_points", ["deleted_at"])

    op.create_table(
        "supply_point_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("supply_point_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_name", sa.String(length=64), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False, server_default="custom"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("icon_key", sa.String(length=64), nullable=True),
        sa.Column("color_key", sa.String(length=32), nullable=True),
        sa.Column("is_custom", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["supply_point_id"], ["supply_points.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_supply_point_items_point", "supply_point_items", ["supply_point_id", "sort_order"])
    op.create_index("idx_supply_point_items_type", "supply_point_items", ["item_type"])
    op.create_index("idx_supply_point_items_status", "supply_point_items", ["status"])
    op.create_index("idx_supply_point_items_deleted_at", "supply_point_items", ["deleted_at"])

    op.create_table(
        "supply_point_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("supply_point_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recorder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("match_status", sa.String(length=32), nullable=False, server_default="matched"),
        sa.Column("display_tone", sa.String(length=32), nullable=False, server_default="success"),
        sa.Column("photo_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("photo_file_url", sa.String(length=1024), nullable=False),
        sa.Column("photo_thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("photo_cos_object_key", sa.String(length=512), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["photo_file_id"], ["file_assets.id"]),
        sa.ForeignKeyConstraint(["recorder_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["supply_point_id"], ["supply_points.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_supply_point_records_point_time", "supply_point_records", ["supply_point_id", sa.text("recorded_at DESC")])
    op.create_index("idx_supply_point_records_recorder", "supply_point_records", ["recorder_id", sa.text("recorded_at DESC")])
    op.create_index("idx_supply_point_records_match", "supply_point_records", ["match_status"])
    op.create_index("idx_supply_point_records_deleted_at", "supply_point_records", ["deleted_at"])

    op.create_table(
        "supply_point_record_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supply_point_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_name", sa.String(length=64), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False, server_default="custom"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("icon_key", sa.String(length=64), nullable=True),
        sa.Column("color_key", sa.String(length=32), nullable=True),
        sa.Column("is_custom", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["record_id"], ["supply_point_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supply_point_item_id"], ["supply_point_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_supply_record_items_record", "supply_point_record_items", ["record_id", "sort_order"])
    op.create_index("idx_supply_record_items_source", "supply_point_record_items", ["supply_point_item_id"])


def downgrade() -> None:
    op.drop_index("idx_supply_record_items_source", table_name="supply_point_record_items")
    op.drop_index("idx_supply_record_items_record", table_name="supply_point_record_items")
    op.drop_table("supply_point_record_items")

    op.drop_index("idx_supply_point_records_deleted_at", table_name="supply_point_records")
    op.drop_index("idx_supply_point_records_match", table_name="supply_point_records")
    op.drop_index("idx_supply_point_records_recorder", table_name="supply_point_records")
    op.drop_index("idx_supply_point_records_point_time", table_name="supply_point_records")
    op.drop_table("supply_point_records")

    op.drop_index("idx_supply_point_items_deleted_at", table_name="supply_point_items")
    op.drop_index("idx_supply_point_items_status", table_name="supply_point_items")
    op.drop_index("idx_supply_point_items_type", table_name="supply_point_items")
    op.drop_index("idx_supply_point_items_point", table_name="supply_point_items")
    op.drop_table("supply_point_items")

    op.drop_index("idx_supply_points_deleted_at", table_name="supply_points")
    op.drop_index("idx_supply_points_updated_by", table_name="supply_points")
    op.drop_index("idx_supply_points_created_by", table_name="supply_points")
    op.drop_index("idx_supply_points_status_public", table_name="supply_points")
    op.drop_index("idx_supply_points_map_point", table_name="supply_points")
    op.drop_index("idx_supply_points_name", table_name="supply_points")
    op.drop_table("supply_points")

    op.execute(
        """
        UPDATE map_marker_configs
        SET business_type = 'food'
        WHERE marker_key = 'supply_food'
        """
    )
