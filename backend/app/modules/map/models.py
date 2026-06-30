from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import Geography


class Campus(Base):
    __tablename__ = "campuses"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128))
    code: Mapped[str | None] = mapped_column(String(64), unique=True)
    center_lng: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    center_lat: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    center_point: Mapped[str | None] = mapped_column(Geography("Point"))
    boundary: Mapped[str | None] = mapped_column(Geography("Polygon"))
    default_zoom: Mapped[int] = mapped_column(Integer, default=16)
    min_zoom: Mapped[int | None] = mapped_column(Integer)
    max_zoom: Mapped[int | None] = mapped_column(Integer)
    map_provider: Mapped[str] = mapped_column(String(32), default="amap")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    areas: Mapped[list["CampusArea"]] = relationship(back_populates="campus")
    points: Mapped[list["MapPoint"]] = relationship(back_populates="campus")


class CampusArea(Base):
    __tablename__ = "campus_areas"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    campus_id: Mapped[UUID] = mapped_column(ForeignKey("campuses.id"))
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("campus_areas.id"))
    name: Mapped[str] = mapped_column(String(128))
    area_type: Mapped[str] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    center_lng: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    center_lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    center_point: Mapped[str | None] = mapped_column(Geography("Point"))
    boundary: Mapped[str | None] = mapped_column(Geography("Polygon"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    campus: Mapped[Campus] = relationship(back_populates="areas")
    points: Mapped[list["MapPoint"]] = relationship(back_populates="area")


class MapMarkerConfig(Base):
    __tablename__ = "map_marker_configs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    marker_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    point_type: Mapped[str] = mapped_column(String(32), index=True)
    business_type: Mapped[str | None] = mapped_column(String(32), index=True)
    label: Mapped[str] = mapped_column(String(64))
    icon_url: Mapped[str | None] = mapped_column(String(512))
    icon_svg: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(32))
    z_index: Mapped[int] = mapped_column(Integer, default=0)
    default_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    default_label_min_zoom: Mapped[int] = mapped_column(Integer, default=17)
    default_preview_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    default_preview_min_zoom: Mapped[int] = mapped_column(Integer, default=17)
    icon_width: Mapped[int | None] = mapped_column(Integer)
    icon_height: Mapped[int | None] = mapped_column(Integer)
    anchor_x: Mapped[int | None] = mapped_column(Integer)
    anchor_y: Mapped[int | None] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class MapPoint(Base):
    __tablename__ = "map_points"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    campus_id: Mapped[UUID] = mapped_column(ForeignKey("campuses.id"), index=True)
    area_id: Mapped[UUID | None] = mapped_column(ForeignKey("campus_areas.id"), index=True)
    point_type: Mapped[str] = mapped_column(String(32), index=True)
    point_scope: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(128))
    subtitle: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    location_name: Mapped[str | None] = mapped_column(String(128))
    location_detail: Mapped[str | None] = mapped_column(Text)
    lng: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    lat: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    geom: Mapped[str] = mapped_column(Geography("Point"))
    amap_poi_id: Mapped[str | None] = mapped_column(String(128))
    amap_address: Mapped[str | None] = mapped_column(String(255))
    tencent_poi_id: Mapped[str | None] = mapped_column(String(128))
    tencent_poi_name: Mapped[str | None] = mapped_column(String(128))
    tencent_poi_address: Mapped[str | None] = mapped_column(String(255))
    tencent_poi_category: Mapped[str | None] = mapped_column(String(128))
    tencent_poi_lng: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    tencent_poi_lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    tencent_poi_distance_meters: Mapped[int | None] = mapped_column(Integer)
    tencent_poi_match_method: Mapped[str | None] = mapped_column(String(32))
    route_instruction: Mapped[str | None] = mapped_column(Text)
    landmark_hint: Mapped[str | None] = mapped_column(Text)
    entrance_hint: Mapped[str | None] = mapped_column(Text)
    icon_key: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("map_marker_configs.marker_key"),
        index=True,
    )
    cover_photo_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    display_level: Mapped[int] = mapped_column(Integer, default=0)
    label_min_zoom: Mapped[int] = mapped_column(Integer, default=17)
    preview_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    preview_min_zoom: Mapped[int] = mapped_column(Integer, default=17)
    visibility: Mapped[str] = mapped_column(String(32), default="public", index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    campus: Mapped[Campus] = relationship(back_populates="points")
    area: Mapped[CampusArea | None] = relationship(back_populates="points")
    photos: Mapped[list["MapPointPhoto"]] = relationship(back_populates="map_point")


class MapPointPhoto(Base):
    __tablename__ = "map_point_photos"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    map_point_id: Mapped[UUID] = mapped_column(ForeignKey("map_points.id"), index=True)
    photo_type: Mapped[str] = mapped_column(String(32), index=True)
    file_url: Mapped[str] = mapped_column(String(512))
    thumbnail_url: Mapped[str | None] = mapped_column(String(512))
    caption: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    map_point: Mapped[MapPoint] = relationship(back_populates="photos")
