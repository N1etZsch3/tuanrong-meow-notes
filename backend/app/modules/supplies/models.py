from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SupplyPoint(Base):
    __tablename__ = "supply_points"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    map_point_id: Mapped[UUID] = mapped_column(ForeignKey("map_points.id"), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    usage_instruction: Mapped[str | None] = mapped_column(Text)
    access_instruction: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    map_point = relationship("MapPoint")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    items: Mapped[list["SupplyPointItem"]] = relationship(
        back_populates="supply_point",
        cascade="all, delete-orphan",
        order_by="SupplyPointItem.sort_order",
    )
    records: Mapped[list["SupplyPointRecord"]] = relationship(
        back_populates="supply_point",
        cascade="all, delete-orphan",
        order_by="SupplyPointRecord.recorded_at.desc()",
    )


class SupplyPointItem(Base):
    __tablename__ = "supply_point_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    supply_point_id: Mapped[UUID] = mapped_column(ForeignKey("supply_points.id"), index=True)
    item_name: Mapped[str] = mapped_column(String(64))
    item_type: Mapped[str] = mapped_column(String(32), default="custom", index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit: Mapped[str | None] = mapped_column(String(32))
    icon_key: Mapped[str | None] = mapped_column(String(64))
    color_key: Mapped[str | None] = mapped_column(String(32))
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    supply_point: Mapped[SupplyPoint] = relationship(back_populates="items")
    record_items: Mapped[list["SupplyPointRecordItem"]] = relationship(
        back_populates="source_item",
    )


class SupplyPointRecord(Base):
    __tablename__ = "supply_point_records"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    supply_point_id: Mapped[UUID] = mapped_column(ForeignKey("supply_points.id"), index=True)
    recorder_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    match_status: Mapped[str] = mapped_column(String(32), default="matched", index=True)
    display_tone: Mapped[str] = mapped_column(String(32), default="success")
    photo_file_id: Mapped[UUID | None] = mapped_column(ForeignKey("file_assets.id"))
    photo_file_url: Mapped[str] = mapped_column(String(1024))
    photo_thumbnail_url: Mapped[str | None] = mapped_column(String(1024))
    photo_cos_object_key: Mapped[str | None] = mapped_column(String(512))
    remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    supply_point: Mapped[SupplyPoint] = relationship(back_populates="records")
    recorder = relationship("User")
    photo_asset = relationship("FileAsset", foreign_keys=[photo_file_id])
    items: Mapped[list["SupplyPointRecordItem"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
        order_by="SupplyPointRecordItem.sort_order",
    )


class SupplyPointRecordItem(Base):
    __tablename__ = "supply_point_record_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    record_id: Mapped[UUID] = mapped_column(ForeignKey("supply_point_records.id"), index=True)
    supply_point_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("supply_point_items.id"),
        index=True,
    )
    item_name: Mapped[str] = mapped_column(String(64))
    item_type: Mapped[str] = mapped_column(String(32), default="custom", index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit: Mapped[str | None] = mapped_column(String(32))
    icon_key: Mapped[str | None] = mapped_column(String(64))
    color_key: Mapped[str | None] = mapped_column(String(32))
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    record: Mapped[SupplyPointRecord] = relationship(back_populates="items")
    source_item: Mapped[SupplyPointItem | None] = relationship(back_populates="record_items")
