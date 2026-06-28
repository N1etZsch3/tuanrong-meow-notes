from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Cat(Base):
    __tablename__ = "cats"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(64), index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    avatar_thumbnail_url: Mapped[str | None] = mapped_column(String(512))
    coat_color: Mapped[str] = mapped_column(String(64), index=True)
    sex: Mapped[str] = mapped_column(String(32), default="unknown")
    neuter_status: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    health_status: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    resident_area_text: Mapped[str] = mapped_column(String(128), index=True)
    primary_area_id: Mapped[UUID | None] = mapped_column(ForeignKey("campus_areas.id"))
    primary_map_point_id: Mapped[UUID | None] = mapped_column(ForeignKey("map_points.id"))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_map_point_id: Mapped[UUID | None] = mapped_column(ForeignKey("map_points.id"))
    personality_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    story: Mapped[str | None] = mapped_column(Text)
    feeding_notes: Mapped[str | None] = mapped_column(Text)
    capture_notes: Mapped[str | None] = mapped_column(Text)
    medical_notes: Mapped[str | None] = mapped_column(Text)
    remark: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    aliases: Mapped[list["CatAlias"]] = relationship(back_populates="cat")
    photos: Mapped[list["CatPhoto"]] = relationship(back_populates="cat")


class CatAlias(Base):
    __tablename__ = "cat_aliases"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    cat_id: Mapped[UUID] = mapped_column(ForeignKey("cats.id"), index=True)
    alias_name: Mapped[str] = mapped_column(String(64), index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    cat: Mapped[Cat] = relationship(back_populates="aliases")


class CatPhoto(Base):
    __tablename__ = "cat_photos"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    cat_id: Mapped[UUID] = mapped_column(ForeignKey("cats.id"), index=True)
    photo_type: Mapped[str] = mapped_column(String(32), index=True)
    file_url: Mapped[str] = mapped_column(String(512))
    thumbnail_url: Mapped[str | None] = mapped_column(String(512))
    is_avatar: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    caption: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    cat: Mapped[Cat] = relationship(back_populates="photos")


class CatMapPoint(Base):
    __tablename__ = "cat_map_points"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    cat_id: Mapped[UUID] = mapped_column(ForeignKey("cats.id"), index=True)
    map_point_id: Mapped[UUID] = mapped_column(ForeignKey("map_points.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(32), index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    confidence_level: Mapped[str] = mapped_column(String(32), default="confirmed")
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class CatObservationRecord(Base):
    __tablename__ = "cat_observation_records"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    cat_id: Mapped[UUID] = mapped_column(ForeignKey("cats.id"), index=True)
    observer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(32), default="manual")
    source_task_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    map_point_id: Mapped[UUID | None] = mapped_column(ForeignKey("map_points.id"))
    location_text: Mapped[str | None] = mapped_column(String(255))
    is_seen: Mapped[bool] = mapped_column(Boolean, default=True)
    cat_condition: Mapped[str] = mapped_column(String(32), default="unknown")
    appetite_status: Mapped[str] = mapped_column(String(32), default="unknown")
    is_injured: Mapped[bool] = mapped_column(Boolean, default=False)
    need_follow_up: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    suggest_task: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class CatHealthRecord(Base):
    __tablename__ = "cat_health_records"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    cat_id: Mapped[UUID] = mapped_column(ForeignKey("cats.id"), index=True)
    record_type: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    related_observation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("cat_observation_records.id")
    )
    related_task_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class CatFavorite(Base):
    __tablename__ = "cat_favorites"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    cat_id: Mapped[UUID] = mapped_column(ForeignKey("cats.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
