"""create summer feeding task tables

Revision ID: 20260629_0009
Revises: 20260627_0008
Create Date: 2026-06-29
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260629_0009"
down_revision = "20260627_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO map_marker_configs (
            id, marker_key, point_type, business_type, label, color, z_index,
            default_visible, default_label_min_zoom, default_preview_enabled,
            default_preview_min_zoom, icon_width, icon_height, anchor_x, anchor_y, sort_order
        )
        VALUES (
            gen_random_uuid(), 'task_feeding', 'task', 'feeding', '喂食任务', '#2f8f35', 85,
            true, 16, true, 16, 34, 34, 17, 32, 15
        )
        ON CONFLICT (marker_key) DO NOTHING
        """
    )

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("task_no", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False, server_default="feeding"),
        sa.Column("task_mode", sa.String(length=32), nullable=False, server_default="recurring"),
        sa.Column("schedule_type", sa.String(length=32), nullable=False, server_default="selected_dates"),
        sa.Column("completion_policy", sa.String(length=32), nullable=False, server_default="per_execution_date"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="in_progress"),
        sa.Column("map_point_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("area_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_cat_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("publisher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("participant_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("route_instruction", sa.Text(), nullable=True),
        sa.Column("required_items", sa.String(length=255), nullable=False, server_default="猫粮、水"),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["area_id"], ["campus_areas.id"]),
        sa.ForeignKeyConstraint(["map_point_id"], ["map_points.id"]),
        sa.ForeignKeyConstraint(["publisher_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["related_cat_id"], ["cats.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_no", name="uq_tasks_task_no"),
    )
    op.create_index("idx_tasks_title", "tasks", ["title"])
    op.create_index("idx_tasks_type_status_published", "tasks", ["task_type", "status", sa.text("published_at DESC")], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_tasks_schedule", "tasks", ["task_mode", "schedule_type", "status"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_tasks_map_point", "tasks", ["map_point_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_tasks_area", "tasks", ["area_id"])
    op.create_index("idx_tasks_publisher", "tasks", ["publisher_id"])
    op.create_index("idx_tasks_start_deadline", "tasks", ["start_at", "deadline_at"])
    op.create_index("idx_tasks_public", "tasks", ["is_public", "status"])
    op.create_index("idx_tasks_deleted_at", "tasks", ["deleted_at"])

    op.create_table(
        "task_execution_dates",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execute_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("completed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checkin_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cancelled_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cancelled_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["completed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_task_execution_dates_task_date", "task_execution_dates", ["task_id", "execute_date"], unique=True, postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_task_execution_dates_task", "task_execution_dates", ["task_id", "execute_date"])
    op.create_index("idx_task_execution_dates_date_status", "task_execution_dates", ["execute_date", "status"])
    op.create_index("idx_task_execution_dates_completed_by", "task_execution_dates", ["completed_by", sa.text("completed_at DESC")], postgresql_where=sa.text("completed_by IS NOT NULL"))
    op.create_index("idx_task_execution_dates_checkin", "task_execution_dates", ["checkin_id"])
    op.create_index("idx_task_execution_dates_deleted_at", "task_execution_dates", ["deleted_at"])

    op.create_table(
        "task_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_url", sa.String(length=1024), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("cos_object_key", sa.String(length=512), nullable=True),
        sa.Column("photo_type", sa.String(length=32), nullable=False, server_default="scene"),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_cover", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["file_assets.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_task_photos_task", "task_photos", ["task_id", "sort_order"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_task_photos_type", "task_photos", ["task_id", "photo_type"])
    op.create_index("uq_task_photos_cover", "task_photos", ["task_id"], unique=True, postgresql_where=sa.text("is_cover = true AND deleted_at IS NULL"))
    op.create_index("idx_task_photos_deleted_at", "task_photos", ["deleted_at"])

    op.create_table(
        "task_checkins",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_execution_date_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("execute_date", sa.Date(), nullable=True),
        sa.Column("submitter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("process_result", sa.Text(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="no_review"),
        sa.Column("checkin_type", sa.String(length=32), nullable=False, server_default="feeding"),
        sa.Column("checkin_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("checkin_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["submitter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["task_execution_date_id"], ["task_execution_dates.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_task_checkins_execution_date", "task_checkins", ["task_execution_date_id"])
    op.create_index("idx_task_checkins_task_execute_date", "task_checkins", ["task_id", "execute_date"])
    op.create_index("idx_task_checkins_submitter_time", "task_checkins", ["submitter_id", sa.text("submitted_at DESC")])
    op.create_index("idx_task_checkins_review_status", "task_checkins", ["review_status"])
    op.create_index("idx_task_checkins_type", "task_checkins", ["checkin_type"])
    op.create_index("idx_task_checkins_deleted_at", "task_checkins", ["deleted_at"])

    op.create_table(
        "task_checkin_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("checkin_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_url", sa.String(length=1024), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["checkin_id"], ["task_checkins.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["file_assets.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_task_checkin_photos_checkin", "task_checkin_photos", ["checkin_id", "sort_order"])
    op.create_index("idx_task_checkin_photos_task", "task_checkin_photos", ["task_id"])
    op.create_index("idx_task_checkin_photos_deleted_at", "task_checkin_photos", ["deleted_at"])

    op.create_table(
        "task_activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_execution_date_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("activity_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["task_execution_date_id"], ["task_execution_dates.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_task_activity_logs_task_time", "task_activity_logs", ["task_id", sa.text("created_at DESC")])
    op.create_index("idx_task_activity_logs_execution_date", "task_activity_logs", ["task_execution_date_id", sa.text("created_at DESC")], postgresql_where=sa.text("task_execution_date_id IS NOT NULL"))
    op.create_index("idx_task_activity_logs_type", "task_activity_logs", ["activity_type"])
    op.create_index("idx_task_activity_logs_actor", "task_activity_logs", ["actor_id"])


def downgrade() -> None:
    op.drop_index("idx_task_activity_logs_actor", table_name="task_activity_logs")
    op.drop_index("idx_task_activity_logs_type", table_name="task_activity_logs")
    op.drop_index("idx_task_activity_logs_execution_date", table_name="task_activity_logs")
    op.drop_index("idx_task_activity_logs_task_time", table_name="task_activity_logs")
    op.drop_table("task_activity_logs")

    op.drop_index("idx_task_checkin_photos_deleted_at", table_name="task_checkin_photos")
    op.drop_index("idx_task_checkin_photos_task", table_name="task_checkin_photos")
    op.drop_index("idx_task_checkin_photos_checkin", table_name="task_checkin_photos")
    op.drop_table("task_checkin_photos")

    op.drop_index("idx_task_checkins_deleted_at", table_name="task_checkins")
    op.drop_index("idx_task_checkins_type", table_name="task_checkins")
    op.drop_index("idx_task_checkins_review_status", table_name="task_checkins")
    op.drop_index("idx_task_checkins_submitter_time", table_name="task_checkins")
    op.drop_index("idx_task_checkins_task_execute_date", table_name="task_checkins")
    op.drop_index("idx_task_checkins_execution_date", table_name="task_checkins")
    op.drop_table("task_checkins")

    op.drop_index("idx_task_photos_deleted_at", table_name="task_photos")
    op.drop_index("uq_task_photos_cover", table_name="task_photos")
    op.drop_index("idx_task_photos_type", table_name="task_photos")
    op.drop_index("idx_task_photos_task", table_name="task_photos")
    op.drop_table("task_photos")

    op.drop_index("idx_task_execution_dates_deleted_at", table_name="task_execution_dates")
    op.drop_index("idx_task_execution_dates_checkin", table_name="task_execution_dates")
    op.drop_index("idx_task_execution_dates_completed_by", table_name="task_execution_dates")
    op.drop_index("idx_task_execution_dates_date_status", table_name="task_execution_dates")
    op.drop_index("idx_task_execution_dates_task", table_name="task_execution_dates")
    op.drop_index("uq_task_execution_dates_task_date", table_name="task_execution_dates")
    op.drop_table("task_execution_dates")

    op.drop_index("idx_tasks_deleted_at", table_name="tasks")
    op.drop_index("idx_tasks_public", table_name="tasks")
    op.drop_index("idx_tasks_start_deadline", table_name="tasks")
    op.drop_index("idx_tasks_publisher", table_name="tasks")
    op.drop_index("idx_tasks_area", table_name="tasks")
    op.drop_index("idx_tasks_map_point", table_name="tasks")
    op.drop_index("idx_tasks_schedule", table_name="tasks")
    op.drop_index("idx_tasks_type_status_published", table_name="tasks")
    op.drop_index("idx_tasks_title", table_name="tasks")
    op.drop_table("tasks")
