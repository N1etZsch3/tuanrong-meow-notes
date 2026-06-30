"""add tencent map poi fields

Revision ID: 20260630_0010
Revises: 20260629_0009
Create Date: 2026-06-30
"""

import sqlalchemy as sa

from alembic import op

revision = "20260630_0010"
down_revision = "20260629_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("map_points", sa.Column("tencent_poi_id", sa.String(length=128), nullable=True))
    op.add_column("map_points", sa.Column("tencent_poi_name", sa.String(length=128), nullable=True))
    op.add_column("map_points", sa.Column("tencent_poi_address", sa.String(length=255), nullable=True))
    op.add_column("map_points", sa.Column("tencent_poi_category", sa.String(length=128), nullable=True))
    op.add_column("map_points", sa.Column("tencent_poi_lng", sa.Numeric(10, 7), nullable=True))
    op.add_column("map_points", sa.Column("tencent_poi_lat", sa.Numeric(10, 7), nullable=True))
    op.add_column("map_points", sa.Column("tencent_poi_distance_meters", sa.Integer(), nullable=True))
    op.add_column("map_points", sa.Column("tencent_poi_match_method", sa.String(length=32), nullable=True))
    op.execute("UPDATE campuses SET map_provider = 'tencent' WHERE map_provider = 'amap'")


def downgrade() -> None:
    op.execute("UPDATE campuses SET map_provider = 'amap' WHERE map_provider = 'tencent'")
    op.drop_column("map_points", "tencent_poi_match_method")
    op.drop_column("map_points", "tencent_poi_distance_meters")
    op.drop_column("map_points", "tencent_poi_lat")
    op.drop_column("map_points", "tencent_poi_lng")
    op.drop_column("map_points", "tencent_poi_category")
    op.drop_column("map_points", "tencent_poi_address")
    op.drop_column("map_points", "tencent_poi_name")
    op.drop_column("map_points", "tencent_poi_id")
