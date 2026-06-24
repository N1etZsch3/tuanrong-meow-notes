"""remove sample map points

Revision ID: 20260624_0004
Revises: 20260624_0003
Create Date: 2026-06-24
"""

from alembic import op

revision = "20260624_0004"
down_revision = "20260624_0003"
branch_labels = None
depends_on = None


SAMPLE_MAP_POINT_IDS = (
    "33333333-3333-4333-8333-333333333301",
    "33333333-3333-4333-8333-333333333302",
    "33333333-3333-4333-8333-333333333303",
    "33333333-3333-4333-8333-333333333304",
    "33333333-3333-4333-8333-333333333305",
)


def upgrade() -> None:
    quoted_ids = ", ".join(f"'{point_id}'" for point_id in SAMPLE_MAP_POINT_IDS)
    op.execute(f"DELETE FROM map_points WHERE id IN ({quoted_ids})")


def downgrade() -> None:
    # Do not restore fake map points when rolling back this cleanup migration.
    pass
