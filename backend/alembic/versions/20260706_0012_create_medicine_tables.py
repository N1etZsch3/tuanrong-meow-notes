"""create medicine management tables

Revision ID: 20260706_0012
Revises: 20260703_0011
Create Date: 2026-07-06
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260706_0012"
down_revision = "20260703_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "medicine_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_medicine_categories_code"),
    )
    op.create_index(
        "uq_medicine_categories_name",
        "medicine_categories",
        ["name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_medicine_categories_enabled", "medicine_categories", ["is_enabled", "sort_order"])
    op.create_index("idx_medicine_categories_deleted_at", "medicine_categories", ["deleted_at"])

    op.create_table(
        "medicine_catalogs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("specification", sa.String(length=128), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("usage_notes", sa.Text(), nullable=True),
        sa.Column("cover_image_url", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("archived_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["archived_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["medicine_categories.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_medicine_catalogs_category", "medicine_catalogs", ["category_id"])
    op.create_index("idx_medicine_catalogs_status", "medicine_catalogs", ["status"])
    op.create_index("idx_medicine_catalogs_created_by", "medicine_catalogs", ["created_by"])
    op.create_index("idx_medicine_catalogs_name", "medicine_catalogs", ["name"])
    op.create_index("idx_medicine_catalogs_deleted_at", "medicine_catalogs", ["deleted_at"])
    op.create_index(
        "uq_medicine_catalogs_name_spec_unit",
        "medicine_catalogs",
        [sa.text("lower(name)"), sa.text("COALESCE(specification, '')"), "unit"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "medicine_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("medicine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alias_name", sa.String(length=128), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["medicine_id"], ["medicine_catalogs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_medicine_aliases_medicine", "medicine_aliases", ["medicine_id"])
    op.create_index("idx_medicine_aliases_name", "medicine_aliases", ["alias_name"])
    op.create_index("idx_medicine_aliases_deleted_at", "medicine_aliases", ["deleted_at"])

    op.create_table(
        "medicine_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("medicine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_url", sa.String(length=512), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=512), nullable=True),
        sa.Column("photo_type", sa.String(length=32), nullable=False, server_default="cover"),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["medicine_id"], ["medicine_catalogs.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_medicine_photos_medicine", "medicine_photos", ["medicine_id", "sort_order"])
    op.create_index("idx_medicine_photos_deleted_at", "medicine_photos", ["deleted_at"])
    op.create_index(
        "uq_medicine_cover_photo",
        "medicine_photos",
        ["medicine_id"],
        unique=True,
        postgresql_where=sa.text("photo_type = 'cover' AND deleted_at IS NULL"),
    )

    op.create_table(
        "medicine_holdings",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("medicine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("holder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_holding_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("admin_creator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("initial_quantity", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_in_quantity", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("current_quantity", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("unit_snapshot", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("last_operation_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("delete_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "initial_quantity >= 0 AND total_in_quantity >= 0 AND current_quantity >= 0",
            name="ck_medicine_holdings_quantity_non_negative",
        ),
        sa.CheckConstraint(
            "total_in_quantity >= current_quantity",
            name="ck_medicine_holdings_total_in_gte_current",
        ),
        sa.ForeignKeyConstraint(["admin_creator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["deleted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["holder_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["medicine_id"], ["medicine_catalogs.id"]),
        sa.ForeignKeyConstraint(["source_holding_id"], ["medicine_holdings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_medicine_holdings_medicine", "medicine_holdings", ["medicine_id"])
    op.create_index("idx_medicine_holdings_holder", "medicine_holdings", ["holder_id"])
    op.create_index("idx_medicine_holdings_status", "medicine_holdings", ["status"])
    op.create_index("idx_medicine_holdings_last_operation", "medicine_holdings", [sa.text("last_operation_at DESC")])
    op.create_index("idx_medicine_holdings_deleted_at", "medicine_holdings", ["deleted_at"])
    op.create_index(
        "uq_medicine_holdings_medicine_holder_active",
        "medicine_holdings",
        ["medicine_id", "holder_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND status IN ('active', 'empty')"),
    )

    op.create_table(
        "medicine_use_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("medicine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("holding_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("applicant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("holder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason_type", sa.String(length=64), nullable=True),
        sa.Column("reason_text", sa.Text(), nullable=False),
        sa.Column("usage_description", sa.Text(), nullable=True),
        sa.Column("requested_use_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("related_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_task_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stock_log_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("quantity > 0", name="ck_medicine_use_applications_quantity_positive"),
        sa.ForeignKeyConstraint(["applicant_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["holder_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["holding_id"], ["medicine_holdings.id"]),
        sa.ForeignKeyConstraint(["medicine_id"], ["medicine_catalogs.id"]),
        sa.ForeignKeyConstraint(["related_task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_medicine_applications_applicant", "medicine_use_applications", ["applicant_id", sa.text("created_at DESC")])
    op.create_index("idx_medicine_applications_holder_status", "medicine_use_applications", ["holder_id", "status", sa.text("created_at DESC")])
    op.create_index("idx_medicine_applications_holding_status", "medicine_use_applications", ["holding_id", "status", sa.text("created_at DESC")])
    op.create_index("idx_medicine_applications_status_expires", "medicine_use_applications", ["status", "expires_at"])
    op.create_index("idx_medicine_applications_task", "medicine_use_applications", ["related_task_id"], postgresql_where=sa.text("related_task_id IS NOT NULL"))
    op.create_index("idx_medicine_applications_deleted_at", "medicine_use_applications", ["deleted_at"])

    op.create_table(
        "medicine_stock_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("medicine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("holding_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operation_type", sa.String(length=32), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("quantity_before", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity_after", sa.Numeric(12, 2), nullable=False),
        sa.Column("related_application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_task_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_holding_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_holding_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason_type", sa.String(length=64), nullable=True),
        sa.Column("reason_text", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("evidence_file_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("display_title", sa.String(length=128), nullable=True),
        sa.Column("display_content", sa.Text(), nullable=True),
        sa.Column("operated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["holding_id"], ["medicine_holdings.id"]),
        sa.ForeignKeyConstraint(["medicine_id"], ["medicine_catalogs.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["related_application_id"], ["medicine_use_applications.id"]),
        sa.ForeignKeyConstraint(["related_task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["source_holding_id"], ["medicine_holdings.id"]),
        sa.ForeignKeyConstraint(["target_holding_id"], ["medicine_holdings.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_medicine_stock_logs_medicine_time", "medicine_stock_logs", ["medicine_id", sa.text("created_at DESC")])
    op.create_index("idx_medicine_stock_logs_holding_time", "medicine_stock_logs", ["holding_id", sa.text("created_at DESC")])
    op.create_index("idx_medicine_stock_logs_operator", "medicine_stock_logs", ["operator_id", sa.text("created_at DESC")])
    op.create_index("idx_medicine_stock_logs_operation_type", "medicine_stock_logs", ["operation_type", sa.text("created_at DESC")])
    op.create_index("idx_medicine_stock_logs_task", "medicine_stock_logs", ["related_task_id"], postgresql_where=sa.text("related_task_id IS NOT NULL"))
    op.create_index("idx_medicine_stock_logs_application", "medicine_stock_logs", ["related_application_id"], postgresql_where=sa.text("related_application_id IS NOT NULL"))

    op.create_foreign_key(
        "fk_medicine_use_applications_stock_log",
        "medicine_use_applications",
        "medicine_stock_logs",
        ["stock_log_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_medicine_use_applications_stock_log", "medicine_use_applications", type_="foreignkey")

    op.drop_index("idx_medicine_stock_logs_application", table_name="medicine_stock_logs")
    op.drop_index("idx_medicine_stock_logs_task", table_name="medicine_stock_logs")
    op.drop_index("idx_medicine_stock_logs_operation_type", table_name="medicine_stock_logs")
    op.drop_index("idx_medicine_stock_logs_operator", table_name="medicine_stock_logs")
    op.drop_index("idx_medicine_stock_logs_holding_time", table_name="medicine_stock_logs")
    op.drop_index("idx_medicine_stock_logs_medicine_time", table_name="medicine_stock_logs")
    op.drop_table("medicine_stock_logs")

    op.drop_index("idx_medicine_applications_deleted_at", table_name="medicine_use_applications")
    op.drop_index("idx_medicine_applications_task", table_name="medicine_use_applications")
    op.drop_index("idx_medicine_applications_status_expires", table_name="medicine_use_applications")
    op.drop_index("idx_medicine_applications_holding_status", table_name="medicine_use_applications")
    op.drop_index("idx_medicine_applications_holder_status", table_name="medicine_use_applications")
    op.drop_index("idx_medicine_applications_applicant", table_name="medicine_use_applications")
    op.drop_table("medicine_use_applications")

    op.drop_index("uq_medicine_holdings_medicine_holder_active", table_name="medicine_holdings")
    op.drop_index("idx_medicine_holdings_deleted_at", table_name="medicine_holdings")
    op.drop_index("idx_medicine_holdings_last_operation", table_name="medicine_holdings")
    op.drop_index("idx_medicine_holdings_status", table_name="medicine_holdings")
    op.drop_index("idx_medicine_holdings_holder", table_name="medicine_holdings")
    op.drop_index("idx_medicine_holdings_medicine", table_name="medicine_holdings")
    op.drop_table("medicine_holdings")

    op.drop_index("uq_medicine_cover_photo", table_name="medicine_photos")
    op.drop_index("idx_medicine_photos_deleted_at", table_name="medicine_photos")
    op.drop_index("idx_medicine_photos_medicine", table_name="medicine_photos")
    op.drop_table("medicine_photos")

    op.drop_index("idx_medicine_aliases_deleted_at", table_name="medicine_aliases")
    op.drop_index("idx_medicine_aliases_name", table_name="medicine_aliases")
    op.drop_index("idx_medicine_aliases_medicine", table_name="medicine_aliases")
    op.drop_table("medicine_aliases")

    op.drop_index("uq_medicine_catalogs_name_spec_unit", table_name="medicine_catalogs")
    op.drop_index("idx_medicine_catalogs_deleted_at", table_name="medicine_catalogs")
    op.drop_index("idx_medicine_catalogs_name", table_name="medicine_catalogs")
    op.drop_index("idx_medicine_catalogs_created_by", table_name="medicine_catalogs")
    op.drop_index("idx_medicine_catalogs_status", table_name="medicine_catalogs")
    op.drop_index("idx_medicine_catalogs_category", table_name="medicine_catalogs")
    op.drop_table("medicine_catalogs")

    op.drop_index("idx_medicine_categories_deleted_at", table_name="medicine_categories")
    op.drop_index("idx_medicine_categories_enabled", table_name="medicine_categories")
    op.drop_index("uq_medicine_categories_name", table_name="medicine_categories")
    op.drop_table("medicine_categories")
