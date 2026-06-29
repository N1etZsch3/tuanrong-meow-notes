from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    task_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(128), index=True)
    task_type: Mapped[str] = mapped_column(String(32), default="feeding", index=True)
    task_mode: Mapped[str] = mapped_column(String(32), default="recurring", index=True)
    schedule_type: Mapped[str] = mapped_column(String(32), default="selected_dates", index=True)
    completion_policy: Mapped[str] = mapped_column(String(32), default="per_execution_date")
    priority: Mapped[str] = mapped_column(String(32), default="normal")
    status: Mapped[str] = mapped_column(String(32), default="in_progress", index=True)
    map_point_id: Mapped[UUID] = mapped_column(ForeignKey("map_points.id"), index=True)
    area_id: Mapped[UUID | None] = mapped_column(ForeignKey("campus_areas.id"), index=True)
    related_cat_id: Mapped[UUID | None] = mapped_column(ForeignKey("cats.id"))
    publisher_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    max_participants: Mapped[int] = mapped_column(Integer, default=1)
    participant_count: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text)
    route_instruction: Mapped[str | None] = mapped_column(Text)
    required_items: Mapped[str] = mapped_column(String(255), default="猫粮、水")
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    map_point = relationship("MapPoint")
    publisher = relationship("User")
    execution_dates: Mapped[list["TaskExecutionDate"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskExecutionDate.execute_date",
    )
    photos: Mapped[list["TaskPhoto"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskPhoto.sort_order",
    )
    activities: Mapped[list["TaskActivityLog"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskActivityLog.created_at.desc()",
    )


class TaskExecutionDate(Base):
    __tablename__ = "task_execution_dates"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), index=True)
    execute_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    completed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    checkin_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    cancelled_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    task: Mapped[Task] = relationship(back_populates="execution_dates")
    completed_user = relationship("User", foreign_keys=[completed_by])


class TaskPhoto(Base):
    __tablename__ = "task_photos"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), index=True)
    file_id: Mapped[UUID | None] = mapped_column(ForeignKey("file_assets.id"))
    file_url: Mapped[str] = mapped_column(String(1024))
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024))
    cos_object_key: Mapped[str | None] = mapped_column(String(512))
    photo_type: Mapped[str] = mapped_column(String(32), default="scene", index=True)
    caption: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    uploaded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    task: Mapped[Task] = relationship(back_populates="photos")


class TaskCheckin(Base):
    __tablename__ = "task_checkins"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), index=True)
    task_execution_date_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("task_execution_dates.id"),
        index=True,
    )
    execute_date: Mapped[date | None] = mapped_column(Date, index=True)
    submitter_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=True)
    process_result: Mapped[str | None] = mapped_column(Text)
    remark: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(32), default="no_review", index=True)
    checkin_type: Mapped[str] = mapped_column(String(32), default="feeding", index=True)
    checkin_lng: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    checkin_lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    submitter = relationship("User")
    execution_date = relationship("TaskExecutionDate")
    photos: Mapped[list["TaskCheckinPhoto"]] = relationship(
        back_populates="checkin",
        cascade="all, delete-orphan",
        order_by="TaskCheckinPhoto.sort_order",
    )


class TaskCheckinPhoto(Base):
    __tablename__ = "task_checkin_photos"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    checkin_id: Mapped[UUID] = mapped_column(ForeignKey("task_checkins.id"), index=True)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), index=True)
    file_id: Mapped[UUID | None] = mapped_column(ForeignKey("file_assets.id"))
    file_url: Mapped[str] = mapped_column(String(1024))
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024))
    caption: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    checkin: Mapped[TaskCheckin] = relationship(back_populates="photos")


class TaskActivityLog(Base):
    __tablename__ = "task_activity_logs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), index=True)
    task_execution_date_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("task_execution_dates.id"),
        index=True,
    )
    activity_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(128))
    content: Mapped[str | None] = mapped_column(Text)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    activity_metadata: Mapped[dict | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    task: Mapped[Task] = relationship(back_populates="activities")
    actor = relationship("User")
