from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FileAsset(Base):
    __tablename__ = "file_assets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    storage_provider: Mapped[str] = mapped_column(String(32), default="tencent_cos")
    bucket: Mapped[str] = mapped_column(String(128))
    region: Mapped[str] = mapped_column(String(64))
    env: Mapped[str] = mapped_column(String(32), default="dev")
    usage_type: Mapped[str] = mapped_column(String(64), index=True)
    owner_type: Mapped[str | None] = mapped_column(String(64), index=True)
    owner_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    source_filename: Mapped[str | None] = mapped_column(String(255))
    source_mime_type: Mapped[str | None] = mapped_column(String(64))
    source_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    source_width: Mapped[int | None] = mapped_column(Integer)
    source_height: Mapped[int | None] = mapped_column(Integer)
    source_checksum_sha256: Mapped[str | None] = mapped_column(String(128), index=True)
    default_variant_key: Mapped[str] = mapped_column(String(64), default="display")
    default_url: Mapped[str | None] = mapped_column(String(1024))
    default_thumb_variant_key: Mapped[str] = mapped_column(String(64), default="thumb_md")
    default_thumb_url: Mapped[str | None] = mapped_column(String(1024))
    process_preset: Mapped[str] = mapped_column(String(64))
    process_status: Mapped[str] = mapped_column(String(32), default="completed", index=True)
    security_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    security_provider: Mapped[str | None] = mapped_column(String(32))
    security_trace_id: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    security_suggest: Mapped[str | None] = mapped_column(String(32))
    security_label: Mapped[int | None] = mapped_column(Integer)
    security_error_code: Mapped[int | None] = mapped_column(Integer)
    security_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    security_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    visibility: Mapped[str] = mapped_column(String(32), default="internal")
    uploaded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    variants: Mapped[list["FileAssetVariant"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="FileAssetVariant.sort_order",
    )


class FileAssetVariant(Base):
    __tablename__ = "file_asset_variants"
    __table_args__ = (
        UniqueConstraint("file_asset_id", "variant_key", name="uq_file_asset_variants_asset_key"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    file_asset_id: Mapped[UUID] = mapped_column(ForeignKey("file_assets.id"), index=True)
    variant_key: Mapped[str] = mapped_column(String(64), index=True)
    object_key: Mapped[str] = mapped_column(String(512), unique=True)
    url: Mapped[str] = mapped_column(String(1024))
    mime_type: Mapped[str] = mapped_column(String(64), default="image/jpeg")
    file_ext: Mapped[str] = mapped_column(String(16), default="jpg")
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    quality: Mapped[int | None] = mapped_column(Integer)
    resize_mode: Mapped[str] = mapped_column(String(32), default="fit")
    checksum_sha256: Mapped[str | None] = mapped_column(String(128))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    asset: Mapped[FileAsset] = relationship(back_populates="variants")
