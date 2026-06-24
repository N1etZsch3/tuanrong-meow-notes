"""create map tables

Revision ID: 20260624_0003
Revises: 20260623_0002
Create Date: 2026-06-24
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260624_0003"
down_revision = "20260623_0002"
branch_labels = None
depends_on = None


class Geography(sa.types.UserDefinedType):
    cache_ok = True

    def __init__(self, geometry_type: str, srid: int = 4326) -> None:
        self.geometry_type = geometry_type
        self.srid = srid

    def get_col_spec(self, **kw) -> str:
        return f"geography({self.geometry_type},{self.srid})"


def upgrade() -> None:
    op.create_table(
        "campuses",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("center_lng", sa.Numeric(10, 7), nullable=False),
        sa.Column("center_lat", sa.Numeric(10, 7), nullable=False),
        sa.Column("center_point", Geography("Point"), nullable=True),
        sa.Column("boundary", Geography("Polygon"), nullable=True),
        sa.Column("default_zoom", sa.Integer(), nullable=False, server_default="16"),
        sa.Column("min_zoom", sa.Integer(), nullable=True),
        sa.Column("max_zoom", sa.Integer(), nullable=True),
        sa.Column("map_provider", sa.String(length=32), nullable=False, server_default="amap"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_campuses_code"),
    )
    op.create_index("idx_campuses_active", "campuses", ["is_active"])
    op.create_index("idx_campuses_boundary", "campuses", ["boundary"], postgresql_using="gist")

    op.create_table(
        "campus_areas",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("area_type", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("center_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("center_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("center_point", Geography("Point"), nullable=True),
        sa.Column("boundary", Geography("Polygon"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["campus_id"], ["campuses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["campus_areas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_campus_areas_boundary", "campus_areas", ["boundary"], postgresql_using="gist")
    op.create_index("idx_campus_areas_campus_visible", "campus_areas", ["campus_id", "is_visible"])
    op.create_index("idx_campus_areas_parent", "campus_areas", ["parent_id"])

    op.create_table(
        "map_marker_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("marker_key", sa.String(length=64), nullable=False),
        sa.Column("point_type", sa.String(length=32), nullable=False),
        sa.Column("business_type", sa.String(length=32), nullable=True),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("icon_url", sa.String(length=512), nullable=True),
        sa.Column("icon_svg", sa.Text(), nullable=True),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.Column("z_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("default_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("default_label_min_zoom", sa.Integer(), nullable=False, server_default="17"),
        sa.Column("default_preview_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("default_preview_min_zoom", sa.Integer(), nullable=False, server_default="17"),
        sa.Column("icon_width", sa.Integer(), nullable=True),
        sa.Column("icon_height", sa.Integer(), nullable=True),
        sa.Column("anchor_x", sa.Integer(), nullable=True),
        sa.Column("anchor_y", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("marker_key", name="uq_map_marker_configs_key"),
    )
    op.create_index("idx_map_marker_configs_type", "map_marker_configs", ["point_type", "business_type"])
    op.create_index("idx_map_marker_configs_visible", "map_marker_configs", ["default_visible", "sort_order"])

    op.create_table(
        "map_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("area_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("point_type", sa.String(length=32), nullable=False),
        sa.Column("point_scope", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("subtitle", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location_name", sa.String(length=128), nullable=True),
        sa.Column("location_detail", sa.Text(), nullable=True),
        sa.Column("lng", sa.Numeric(10, 7), nullable=False),
        sa.Column("lat", sa.Numeric(10, 7), nullable=False),
        sa.Column("geom", Geography("Point"), nullable=False),
        sa.Column("amap_poi_id", sa.String(length=128), nullable=True),
        sa.Column("amap_address", sa.String(length=255), nullable=True),
        sa.Column("route_instruction", sa.Text(), nullable=True),
        sa.Column("landmark_hint", sa.Text(), nullable=True),
        sa.Column("entrance_hint", sa.Text(), nullable=True),
        sa.Column("icon_key", sa.String(length=64), nullable=True),
        sa.Column("cover_photo_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("display_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("label_min_zoom", sa.Integer(), nullable=False, server_default="17"),
        sa.Column("preview_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("preview_min_zoom", sa.Integer(), nullable=False, server_default="17"),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="public"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["area_id"], ["campus_areas.id"]),
        sa.ForeignKeyConstraint(["campus_id"], ["campuses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["icon_key"], ["map_marker_configs.marker_key"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_map_points_active_public", "map_points", ["campus_id", "point_type"], postgresql_where=sa.text("status = 'active' AND visibility = 'public' AND deleted_at IS NULL"))
    op.create_index("idx_map_points_area", "map_points", ["area_id"])
    op.create_index("idx_map_points_campus_type_status", "map_points", ["campus_id", "point_type", "status"])
    op.create_index("idx_map_points_created_by", "map_points", ["created_by"])
    op.create_index("idx_map_points_display", "map_points", ["campus_id", sa.text("display_level DESC"), "preview_enabled", "preview_min_zoom"])
    op.create_index("idx_map_points_geom", "map_points", ["geom"], postgresql_using="gist")
    op.create_index("idx_map_points_icon_key", "map_points", ["icon_key"])
    op.create_index("idx_map_points_visible", "map_points", ["visibility", "status"])

    op.create_table(
        "map_point_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("map_point_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("photo_type", sa.String(length=32), nullable=False),
        sa.Column("file_url", sa.String(length=512), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=512), nullable=True),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["map_point_id"], ["map_points.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_map_point_photos_point", "map_point_photos", ["map_point_id"])
    op.create_index("idx_map_point_photos_type", "map_point_photos", ["photo_type"])

    op.create_foreign_key(
        "fk_map_points_cover_photo_id",
        "map_points",
        "map_point_photos",
        ["cover_photo_id"],
        ["id"],
    )

    seed_map_data()


def seed_map_data() -> None:
    op.execute(
        """
        INSERT INTO campuses (
            id, code, name, center_lng, center_lat, center_point, boundary,
            default_zoom, min_zoom, max_zoom, map_provider, is_active
        )
        VALUES (
            '11111111-1111-4111-8111-111111111111',
            'hbnu_main',
            '湖北师范大学',
            115.0622020,
            30.2299100,
            ST_SetSRID(ST_MakePoint(115.0622020, 30.2299100), 4326)::geography,
            ST_GeogFromText('SRID=4326;POLYGON((115.0558 30.2248,115.0693 30.2248,115.0693 30.2342,115.0558 30.2342,115.0558 30.2248))'),
            17,
            15,
            20,
            'amap',
            true
        )
        """
    )
    op.execute(
        """
        INSERT INTO campus_areas (
            id, campus_id, name, area_type, description, center_lng, center_lat,
            center_point, sort_order, is_visible
        )
        VALUES
        ('22222222-2222-4222-8222-222222222201', '11111111-1111-4111-8111-111111111111', '北门', 'gate', '北门及周边草丛区域', 115.0602000, 30.2332000, ST_SetSRID(ST_MakePoint(115.0602000, 30.2332000), 4326)::geography, 10, true),
        ('22222222-2222-4222-8222-222222222202', '11111111-1111-4111-8111-111111111111', '食堂', 'canteen', '食堂后方投喂清洁区域', 115.0617000, 30.2315000, ST_SetSRID(ST_MakePoint(115.0617000, 30.2315000), 4326)::geography, 20, true),
        ('22222222-2222-4222-8222-222222222203', '11111111-1111-4111-8111-111111111111', '教学楼B', 'teaching_building', '教学楼B及右侧草坪', 115.0632000, 30.2308000, ST_SetSRID(ST_MakePoint(115.0632000, 30.2308000), 4326)::geography, 30, true),
        ('22222222-2222-4222-8222-222222222204', '11111111-1111-4111-8111-111111111111', '体育馆', 'gym', '体育馆旁物资补给区域', 115.0642000, 30.2287000, ST_SetSRID(ST_MakePoint(115.0642000, 30.2287000), 4326)::geography, 40, true),
        ('22222222-2222-4222-8222-222222222205', '11111111-1111-4111-8111-111111111111', '图书馆', 'landmark', '图书馆及附近路线', 115.0618000, 30.2291000, ST_SetSRID(ST_MakePoint(115.0618000, 30.2291000), 4326)::geography, 50, true)
        """
    )
    op.execute(
        """
        INSERT INTO map_marker_configs (
            id, marker_key, point_type, business_type, label, color, z_index,
            default_visible, default_label_min_zoom, default_preview_enabled,
            default_preview_min_zoom, icon_width, icon_height, anchor_x, anchor_y, sort_order
        )
        VALUES
        ('44444444-4444-4444-8444-444444444401', 'task_emergency', 'task', 'emergency', '紧急任务', '#ef3038', 100, true, 16, true, 16, 36, 36, 18, 34, 10),
        ('44444444-4444-4444-8444-444444444402', 'task_daily', 'task', 'daily', '日常任务', '#2f7cf6', 80, true, 17, true, 17, 32, 32, 16, 30, 20),
        ('44444444-4444-4444-8444-444444444403', 'cat_home', 'cat', 'resident', '猫咪点', '#8754e8', 60, true, 17, true, 17, 32, 32, 16, 30, 30),
        ('44444444-4444-4444-8444-444444444404', 'supply_food', 'supply', 'food', '物资点', '#ff8b22', 50, true, 17, false, 17, 32, 32, 16, 30, 40),
        ('44444444-4444-4444-8444-444444444405', 'landmark_library', 'landmark', 'library', '地标', '#28a745', 20, true, 17, false, 17, 28, 28, 14, 26, 50)
        """
    )
    op.execute(
        """
        INSERT INTO map_points (
            id, campus_id, area_id, point_type, point_scope, name, subtitle, description,
            location_name, location_detail, lng, lat, geom, amap_poi_id, amap_address,
            route_instruction, landmark_hint, entrance_hint, icon_key, display_level,
            label_min_zoom, preview_enabled, preview_min_zoom, visibility, status
        )
        VALUES
        (
            '33333333-3333-4333-8333-333333333301',
            '11111111-1111-4111-8111-111111111111',
            '22222222-2222-4222-8222-222222222201',
            'task',
            'temporary',
            '北门草丛紧急救助任务',
            '发现受伤流浪猫',
            '北门草丛中发现受伤流浪猫，需要紧急救助和医疗处理。',
            '北门草丛',
            '北门进门右侧草丛附近',
            115.0609000,
            30.2330000,
            ST_SetSRID(ST_MakePoint(115.0609000, 30.2330000), 4326)::geography,
            null,
            '湖北省黄石市湖北师范大学北门附近',
            '到达北门后沿右侧小路向内走约 30 米。',
            '靠近北门保安亭',
            '从北门进入最近',
            'task_emergency',
            100,
            16,
            true,
            16,
            'public',
            'active'
        ),
        (
            '33333333-3333-4333-8333-333333333302',
            '11111111-1111-4111-8111-111111111111',
            '22222222-2222-4222-8222-222222222202',
            'task',
            'temporary',
            '食堂后方投喂清洁',
            '日常投喂与清理',
            '清理食堂后方投喂点，补充少量猫粮并检查水碗。',
            '食堂后方',
            '食堂后门外侧靠近绿化带的位置',
            115.0617000,
            30.2315000,
            ST_SetSRID(ST_MakePoint(115.0617000, 30.2315000), 4326)::geography,
            null,
            '湖北省黄石市湖北师范大学食堂附近',
            '从食堂后门出来后沿绿化带向东走约 20 米。',
            '靠近食堂后门',
            '从食堂后门进入最近',
            'task_daily',
            80,
            17,
            true,
            17,
            'public',
            'active'
        ),
        (
            '33333333-3333-4333-8333-333333333303',
            '11111111-1111-4111-8111-111111111111',
            '22222222-2222-4222-8222-222222222203',
            'cat',
            'long_term',
            '小橘常驻点',
            '教学楼B附近',
            '常驻猫咪，性格亲人，常在教学楼B右侧草坪活动。',
            '教学楼B右侧草坪',
            '教学楼B右侧靠近灌木的位置',
            115.0632000,
            30.2308000,
            ST_SetSRID(ST_MakePoint(115.0632000, 30.2308000), 4326)::geography,
            null,
            '湖北省黄石市湖北师范大学教学楼B附近',
            '从教学楼B正门向右侧草坪方向走。',
            '靠近教学楼B',
            '从教学楼B正门进入最近',
            'cat_home',
            40,
            17,
            true,
            17,
            'public',
            'active'
        ),
        (
            '33333333-3333-4333-8333-333333333304',
            '11111111-1111-4111-8111-111111111111',
            '22222222-2222-4222-8222-222222222204',
            'supply',
            'long_term',
            '猫协物资点 #1',
            '体育馆旁物资补给',
            '猫粮、航空箱、诱捕笼备用点。',
            '体育馆旁',
            '体育馆东侧储物点附近',
            115.0642000,
            30.2287000,
            ST_SetSRID(ST_MakePoint(115.0642000, 30.2287000), 4326)::geography,
            null,
            '湖北省黄石市湖北师范大学体育馆附近',
            '从体育馆东侧道路进入，靠近储物点。',
            '靠近体育馆',
            '从体育馆东门进入最近',
            'supply_food',
            30,
            17,
            false,
            17,
            'public',
            'active'
        ),
        (
            '33333333-3333-4333-8333-333333333305',
            '11111111-1111-4111-8111-111111111111',
            '22222222-2222-4222-8222-222222222205',
            'landmark',
            'long_term',
            '图书馆',
            '校园地标',
            '图书馆附近有常见投喂路线和临时观察点。',
            '图书馆',
            '图书馆主入口附近',
            115.0618000,
            30.2291000,
            ST_SetSRID(ST_MakePoint(115.0618000, 30.2291000), 4326)::geography,
            null,
            '湖北省黄石市湖北师范大学图书馆',
            '从图书馆主入口向外侧步道查看周边观察点。',
            '图书馆主楼',
            '从图书馆主入口进入最近',
            'landmark_library',
            20,
            17,
            false,
            17,
            'public',
            'active'
        )
        """
    )


def downgrade() -> None:
    op.drop_constraint("fk_map_points_cover_photo_id", "map_points", type_="foreignkey")
    op.drop_index("idx_map_point_photos_type", table_name="map_point_photos")
    op.drop_index("idx_map_point_photos_point", table_name="map_point_photos")
    op.drop_table("map_point_photos")
    op.drop_index("idx_map_points_visible", table_name="map_points")
    op.drop_index("idx_map_points_icon_key", table_name="map_points")
    op.drop_index("idx_map_points_geom", table_name="map_points")
    op.drop_index("idx_map_points_display", table_name="map_points")
    op.drop_index("idx_map_points_created_by", table_name="map_points")
    op.drop_index("idx_map_points_campus_type_status", table_name="map_points")
    op.drop_index("idx_map_points_area", table_name="map_points")
    op.drop_index("idx_map_points_active_public", table_name="map_points")
    op.drop_table("map_points")
    op.drop_index("idx_map_marker_configs_visible", table_name="map_marker_configs")
    op.drop_index("idx_map_marker_configs_type", table_name="map_marker_configs")
    op.drop_table("map_marker_configs")
    op.drop_index("idx_campus_areas_parent", table_name="campus_areas")
    op.drop_index("idx_campus_areas_campus_visible", table_name="campus_areas")
    op.drop_index("idx_campus_areas_boundary", table_name="campus_areas")
    op.drop_table("campus_areas")
    op.drop_index("idx_campuses_boundary", table_name="campuses")
    op.drop_index("idx_campuses_active", table_name="campuses")
    op.drop_table("campuses")
