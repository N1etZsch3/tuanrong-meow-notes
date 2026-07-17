from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    student_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="member", index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    password_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    login_failed_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    wechat_openid: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    wechat_bound_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_wechat_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    departments: Mapped[list["UserDepartment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="UserDepartment.sort_order",
    )


class UserDepartment(Base):
    __tablename__ = "user_departments"
    __table_args__ = (
        UniqueConstraint("user_id", "department", name="uq_user_departments_user_department"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    department: Mapped[str] = mapped_column(String(128))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="departments")


class AuthCaptcha(Base):
    __tablename__ = "auth_captchas"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    code_hash: Mapped[str] = mapped_column(String(255))
    scene: Mapped[str] = mapped_column(String(32), default="login", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    client_ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        # 12 个非 none 头衔全局唯一：部分唯一索引仅约束 title 非空的行
        Index(
            "uq_user_profiles_title",
            "title",
            unique=True,
            sqlite_where=text("title IS NOT NULL"),
            postgresql_where=text("title IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    nickname: Mapped[str] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    avatar_asset_id: Mapped[UUID | None] = mapped_column(ForeignKey("file_assets.id"))
    avatar_thumb_url: Mapped[str | None] = mapped_column(String(1024))
    avatar_review_asset_id: Mapped[UUID | None] = mapped_column(ForeignKey("file_assets.id"))
    avatar_review_status: Mapped[str] = mapped_column(String(32), default="idle")
    avatar_review_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    real_name: Mapped[str | None] = mapped_column(String(64))
    department: Mapped[str | None] = mapped_column(String(128))
    title: Mapped[str | None] = mapped_column(String(64))
    grade: Mapped[str | None] = mapped_column(String(32))
    joined_at: Mapped[date | None] = mapped_column(Date)
    bio: Mapped[str | None] = mapped_column(Text)
    contact_info: Mapped[str | None] = mapped_column(String(128))
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="profile")


class AdminOperationLog(Base):
    __tablename__ = "admin_operation_logs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    admin_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    operation_type: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    summary: Mapped[str | None] = mapped_column(String(255))
    before_data: Mapped[dict | None] = mapped_column(JSON)
    after_data: Mapped[dict | None] = mapped_column(JSON)
    client_ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
