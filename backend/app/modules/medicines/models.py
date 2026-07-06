from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MedicineCategory(Base):
    __tablename__ = "medicine_categories"
    __table_args__ = (
        Index(
            "uq_medicine_categories_name",
            "name",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(64))
    code: Mapped[str | None] = mapped_column(String(64), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    catalogs: Mapped[list["MedicineCatalog"]] = relationship(back_populates="category")


class MedicineCatalog(Base):
    __tablename__ = "medicine_catalogs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), index=True)
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("medicine_categories.id"),
        index=True,
    )
    specification: Mapped[str | None] = mapped_column(String(128))
    unit: Mapped[str] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    usage_notes: Mapped[str | None] = mapped_column(Text)
    cover_image_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    archived_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archive_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    category: Mapped[MedicineCategory | None] = relationship(back_populates="catalogs")
    holdings: Mapped[list["MedicineHolding"]] = relationship(back_populates="medicine")
    logs: Mapped[list["MedicineStockLog"]] = relationship(back_populates="medicine")


class MedicineAlias(Base):
    __tablename__ = "medicine_aliases"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    medicine_id: Mapped[UUID] = mapped_column(ForeignKey("medicine_catalogs.id"), index=True)
    alias_name: Mapped[str] = mapped_column(String(128), index=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    medicine: Mapped[MedicineCatalog] = relationship()


class MedicinePhoto(Base):
    __tablename__ = "medicine_photos"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    medicine_id: Mapped[UUID] = mapped_column(ForeignKey("medicine_catalogs.id"), index=True)
    file_url: Mapped[str] = mapped_column(String(512))
    thumbnail_url: Mapped[str | None] = mapped_column(String(512))
    photo_type: Mapped[str] = mapped_column(String(32), default="cover", index=True)
    caption: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    medicine: Mapped[MedicineCatalog] = relationship()


class MedicineHolding(Base):
    __tablename__ = "medicine_holdings"
    __table_args__ = (
        CheckConstraint(
            "initial_quantity >= 0 AND total_in_quantity >= 0 AND current_quantity >= 0",
            name="ck_medicine_holdings_quantity_non_negative",
        ),
        CheckConstraint(
            "total_in_quantity >= current_quantity",
            name="ck_medicine_holdings_total_in_gte_current",
        ),
        Index(
            "uq_medicine_holdings_medicine_holder_active",
            "medicine_id",
            "holder_id",
            unique=True,
            sqlite_where=text("deleted_at IS NULL AND status IN ('active', 'empty')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    medicine_id: Mapped[UUID] = mapped_column(ForeignKey("medicine_catalogs.id"), index=True)
    holder_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    source_holding_id: Mapped[UUID | None] = mapped_column(ForeignKey("medicine_holdings.id"))
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    admin_creator_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    initial_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_in_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    current_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    unit_snapshot: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    last_operation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    remark: Mapped[str | None] = mapped_column(Text)
    deleted_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    delete_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    medicine: Mapped[MedicineCatalog] = relationship(back_populates="holdings")
    holder = relationship("User", foreign_keys=[holder_id])
    logs: Mapped[list["MedicineStockLog"]] = relationship(
        back_populates="holding",
        foreign_keys="MedicineStockLog.holding_id",
    )


class MedicineStockLog(Base):
    __tablename__ = "medicine_stock_logs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    medicine_id: Mapped[UUID] = mapped_column(ForeignKey("medicine_catalogs.id"), index=True)
    holding_id: Mapped[UUID | None] = mapped_column(ForeignKey("medicine_holdings.id"), index=True)
    operator_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    operation_type: Mapped[str] = mapped_column(String(32), index=True)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    related_application_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("medicine_use_applications.id"),
        index=True,
    )
    related_task_id: Mapped[UUID | None] = mapped_column(ForeignKey("tasks.id"), index=True)
    related_task_snapshot: Mapped[dict | None] = mapped_column(JSON)
    target_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    source_holding_id: Mapped[UUID | None] = mapped_column(ForeignKey("medicine_holdings.id"))
    target_holding_id: Mapped[UUID | None] = mapped_column(ForeignKey("medicine_holdings.id"))
    reason_type: Mapped[str | None] = mapped_column(String(64))
    reason_text: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    remark: Mapped[str | None] = mapped_column(Text)
    evidence_file_ids: Mapped[list | None] = mapped_column(JSON)
    display_title: Mapped[str | None] = mapped_column(String(128))
    display_content: Mapped[str | None] = mapped_column(Text)
    operated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    medicine: Mapped[MedicineCatalog] = relationship(back_populates="logs")
    holding: Mapped[MedicineHolding | None] = relationship(
        back_populates="logs",
        foreign_keys=[holding_id],
    )
    operator = relationship("User", foreign_keys=[operator_id])


class MedicineUseApplication(Base):
    __tablename__ = "medicine_use_applications"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_medicine_use_applications_quantity_positive"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    medicine_id: Mapped[UUID] = mapped_column(ForeignKey("medicine_catalogs.id"), index=True)
    holding_id: Mapped[UUID] = mapped_column(ForeignKey("medicine_holdings.id"), index=True)
    applicant_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    holder_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    reason_type: Mapped[str | None] = mapped_column(String(64))
    reason_text: Mapped[str] = mapped_column(Text)
    usage_description: Mapped[str | None] = mapped_column(Text)
    requested_use_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    related_task_id: Mapped[UUID | None] = mapped_column(ForeignKey("tasks.id"), index=True)
    related_task_snapshot: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    reviewer_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    review_comment: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stock_log_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("medicine_stock_logs.id", use_alter=True),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    medicine: Mapped[MedicineCatalog] = relationship()
    holding: Mapped[MedicineHolding] = relationship()
    applicant = relationship("User", foreign_keys=[applicant_id])
    holder = relationship("User", foreign_keys=[holder_id])
