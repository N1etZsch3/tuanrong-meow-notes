"""create wechat guests table

Revision ID: 20260712_0015
Revises: 20260712_0014
Create Date: 2026-07-12
"""

import sqlalchemy as sa

from alembic import op

revision = "20260712_0015"
down_revision = "20260712_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wechat_guests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("openid", sa.String(length=128), nullable=False),
        sa.Column("visit_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "first_visit_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_visit_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_wechat_guests_openid",
        "wechat_guests",
        ["openid"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_wechat_guests_openid", table_name="wechat_guests")
    op.drop_table("wechat_guests")
