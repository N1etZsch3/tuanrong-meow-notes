from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    """成员通知（《用户与个人中心模块_库表设计文档》notifications 表）。"""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "is_read"),
        Index("idx_notifications_user_created", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    notification_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, default="")
    related_type: Mapped[str | None] = mapped_column(String(64))
    related_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class UserNotificationSetting(Base):
    """成员通知接收开关（按前端喵息页 7 个展示频道分组）。"""

    __tablename__ = "user_notification_settings"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    task_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    feeding_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    medicine_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    supply_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    member_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    cat_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    announcement_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
