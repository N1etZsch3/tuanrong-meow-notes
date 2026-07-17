"""create user_departments table and backfill from profile.department

Revision ID: 20260717_0017
Revises: 20260716_0016
Create Date: 2026-07-17
"""

import sqlalchemy as sa

from alembic import op

revision = "20260717_0017"
down_revision = "20260716_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_departments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("department", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
            name="fk_user_departments_user_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "department", name="uq_user_departments_user_department"
        ),
    )
    op.create_index(
        "idx_user_departments_user_id",
        "user_departments",
        ["user_id"],
    )

    # 回填：把每个 user_profiles.department 非空的行迁入关联表作为主部门（sort_order=0）。
    # profile.department 单列保留不动，作为兼容旧客户端的主部门字段。
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        id_expr = "gen_random_uuid()"
        now_expr = "now()"
    else:
        # SQLite（测试）用 hex 拼接生成随机 uuid 文本
        id_expr = (
            "lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || "
            "substr(hex(randomblob(2)),2) || '-' || substr('89ab', abs(random()) % 4 + 1, 1) || "
            "substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))"
        )
        now_expr = "CURRENT_TIMESTAMP"
    op.execute(
        sa.text(
            f"""
            INSERT INTO user_departments (id, user_id, department, sort_order, created_at)
            SELECT {id_expr}, user_id, department, 0, {now_expr}
            FROM user_profiles
            WHERE department IS NOT NULL AND trim(department) <> ''
            """
        )
    )


def downgrade() -> None:
    # profile.department 数据不受影响，仅回收关联表。
    op.drop_index("idx_user_departments_user_id", table_name="user_departments")
    op.drop_table("user_departments")
