"""create cat archive tables

Revision ID: 20260627_0008
Revises: 20260627_0007
Create Date: 2026-06-27
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260627_0008"
down_revision = "20260627_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cats",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("avatar_thumbnail_url", sa.String(length=512), nullable=True),
        sa.Column("coat_color", sa.String(length=64), nullable=False),
        sa.Column("sex", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("neuter_status", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("health_status", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("resident_area_text", sa.String(length=128), nullable=False),
        sa.Column("primary_area_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("primary_map_point_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_map_point_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("personality_tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("story", sa.Text(), nullable=True),
        sa.Column("feeding_notes", sa.Text(), nullable=True),
        sa.Column("capture_notes", sa.Text(), nullable=True),
        sa.Column("medical_notes", sa.Text(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["last_seen_map_point_id"], ["map_points.id"]),
        sa.ForeignKeyConstraint(["primary_area_id"], ["campus_areas.id"]),
        sa.ForeignKeyConstraint(["primary_map_point_id"], ["map_points.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cats_name", "cats", ["name"])
    op.create_index("idx_cats_status", "cats", ["status"])
    op.create_index("idx_cats_health_status", "cats", ["health_status"])
    op.create_index("idx_cats_neuter_status", "cats", ["neuter_status"])
    op.create_index("idx_cats_coat_color", "cats", ["coat_color"])
    op.create_index("idx_cats_resident_area_text", "cats", ["resident_area_text"])
    op.create_index("idx_cats_last_seen_at", "cats", ["last_seen_at"])
    op.create_index("idx_cats_deleted_at", "cats", ["deleted_at"])

    op.create_table(
        "cat_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alias_name", sa.String(length=64), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cat_id"], ["cats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cat_aliases_cat", "cat_aliases", ["cat_id"])
    op.create_index("idx_cat_aliases_name", "cat_aliases", ["alias_name"])
    op.create_index("idx_cat_aliases_deleted_at", "cat_aliases", ["deleted_at"])

    op.create_table(
        "cat_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("photo_type", sa.String(length=32), nullable=False),
        sa.Column("file_url", sa.String(length=512), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=512), nullable=True),
        sa.Column("is_avatar", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cat_id"], ["cats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cat_photos_cat", "cat_photos", ["cat_id", "sort_order"])
    op.create_index("idx_cat_photos_type", "cat_photos", ["cat_id", "photo_type"])
    op.create_index("idx_cat_photos_avatar", "cat_photos", ["cat_id", "is_avatar"])
    op.create_index("idx_cat_photos_deleted_at", "cat_photos", ["deleted_at"])

    op.create_table(
        "cat_map_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("map_point_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(length=32), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("confidence_level", sa.String(length=32), nullable=False, server_default="confirmed"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cat_id"], ["cats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["map_point_id"], ["map_points.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cat_map_points_cat", "cat_map_points", ["cat_id"])
    op.create_index("idx_cat_map_points_point", "cat_map_points", ["map_point_id"])
    op.create_index("idx_cat_map_points_relation", "cat_map_points", ["relation_type"])
    op.create_index("idx_cat_map_points_primary", "cat_map_points", ["cat_id", "is_primary"])
    op.create_index("idx_cat_map_points_deleted_at", "cat_map_points", ["deleted_at"])

    op.create_table(
        "cat_observation_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("source_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("map_point_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location_text", sa.String(length=255), nullable=True),
        sa.Column("is_seen", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("cat_condition", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("appetite_status", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("is_injured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("need_follow_up", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("suggest_task", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cat_id"], ["cats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["map_point_id"], ["map_points.id"]),
        sa.ForeignKeyConstraint(["observer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cat_observations_cat_time", "cat_observation_records", ["cat_id", "observed_at"])
    op.create_index("idx_cat_observations_observer", "cat_observation_records", ["observer_id", "observed_at"])
    op.create_index("idx_cat_observations_need_follow", "cat_observation_records", ["need_follow_up"])
    op.create_index("idx_cat_observations_deleted_at", "cat_observation_records", ["deleted_at"])

    op.create_table(
        "cat_health_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("related_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cat_id"], ["cats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["related_observation_id"], ["cat_observation_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cat_health_records_cat_time", "cat_health_records", ["cat_id", "recorded_at"])
    op.create_index("idx_cat_health_records_type", "cat_health_records", ["record_type"])
    op.create_index("idx_cat_health_records_deleted_at", "cat_health_records", ["deleted_at"])

    op.create_table(
        "cat_favorites",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cat_id"], ["cats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cat_favorites_user", "cat_favorites", ["user_id", "created_at"])
    op.create_index("idx_cat_favorites_cat", "cat_favorites", ["cat_id"])
    op.create_index("idx_cat_favorites_deleted_at", "cat_favorites", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_cat_favorites_deleted_at", table_name="cat_favorites")
    op.drop_index("idx_cat_favorites_cat", table_name="cat_favorites")
    op.drop_index("idx_cat_favorites_user", table_name="cat_favorites")
    op.drop_table("cat_favorites")

    op.drop_index("idx_cat_health_records_deleted_at", table_name="cat_health_records")
    op.drop_index("idx_cat_health_records_type", table_name="cat_health_records")
    op.drop_index("idx_cat_health_records_cat_time", table_name="cat_health_records")
    op.drop_table("cat_health_records")

    op.drop_index("idx_cat_observations_deleted_at", table_name="cat_observation_records")
    op.drop_index("idx_cat_observations_need_follow", table_name="cat_observation_records")
    op.drop_index("idx_cat_observations_observer", table_name="cat_observation_records")
    op.drop_index("idx_cat_observations_cat_time", table_name="cat_observation_records")
    op.drop_table("cat_observation_records")

    op.drop_index("idx_cat_map_points_deleted_at", table_name="cat_map_points")
    op.drop_index("idx_cat_map_points_primary", table_name="cat_map_points")
    op.drop_index("idx_cat_map_points_relation", table_name="cat_map_points")
    op.drop_index("idx_cat_map_points_point", table_name="cat_map_points")
    op.drop_index("idx_cat_map_points_cat", table_name="cat_map_points")
    op.drop_table("cat_map_points")

    op.drop_index("idx_cat_photos_deleted_at", table_name="cat_photos")
    op.drop_index("idx_cat_photos_avatar", table_name="cat_photos")
    op.drop_index("idx_cat_photos_type", table_name="cat_photos")
    op.drop_index("idx_cat_photos_cat", table_name="cat_photos")
    op.drop_table("cat_photos")

    op.drop_index("idx_cat_aliases_deleted_at", table_name="cat_aliases")
    op.drop_index("idx_cat_aliases_name", table_name="cat_aliases")
    op.drop_index("idx_cat_aliases_cat", table_name="cat_aliases")
    op.drop_table("cat_aliases")

    op.drop_index("idx_cats_deleted_at", table_name="cats")
    op.drop_index("idx_cats_last_seen_at", table_name="cats")
    op.drop_index("idx_cats_resident_area_text", table_name="cats")
    op.drop_index("idx_cats_coat_color", table_name="cats")
    op.drop_index("idx_cats_neuter_status", table_name="cats")
    op.drop_index("idx_cats_health_status", table_name="cats")
    op.drop_index("idx_cats_status", table_name="cats")
    op.drop_index("idx_cats_name", table_name="cats")
    op.drop_table("cats")
