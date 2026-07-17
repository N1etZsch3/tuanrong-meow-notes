from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import APIError, ErrorCode
from app.modules.auth.models import User
from app.modules.notifications.models import Notification, UserNotificationSetting

SETTING_FIELDS = (
    "task_enabled",
    "feeding_enabled",
    "medicine_enabled",
    "supply_enabled",
    "member_enabled",
    "cat_enabled",
    "announcement_enabled",
)


def notification_payload(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "notification_type": notification.notification_type,
        "title": notification.title,
        "content": notification.content,
        "related_type": notification.related_type,
        "related_id": notification.related_id,
        "is_read": notification.is_read,
        "read_at": notification.read_at,
        "created_at": notification.created_at,
    }


def list_notifications(
    db: Session,
    *,
    user: User,
    is_read: bool | None = None,
    notification_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    statement = select(Notification).where(Notification.user_id == user.id)
    if is_read is not None:
        statement = statement.where(Notification.is_read.is_(is_read))
    if notification_type:
        statement = statement.where(Notification.notification_type == notification_type)

    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    start = (page - 1) * page_size
    items = db.scalars(
        statement.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(start)
        .limit(page_size)
    ).all()
    return {
        "items": [notification_payload(item) for item in items],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": start + page_size < total,
    }


def unread_count(db: Session, *, user: User) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.is_read.is_(False))
        )
        or 0
    )


def mark_read(db: Session, *, user: User, notification_id: UUID) -> dict:
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise APIError(
            code=ErrorCode.NOTIFICATION_NOT_FOUND,
            message="通知不存在",
            status_code=404,
        )
    if notification.user_id != user.id:
        raise APIError(
            code=ErrorCode.NOTIFICATION_FORBIDDEN,
            message="不能操作他人的通知",
            status_code=403,
        )
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        db.commit()
        db.refresh(notification)
    return {
        "id": notification.id,
        "is_read": notification.is_read,
        "read_at": notification.read_at,
    }


def mark_all_read(db: Session, *, user: User) -> dict:
    now = datetime.now(UTC)
    unread = db.scalars(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.is_read.is_(False),
        )
    ).all()
    for notification in unread:
        notification.is_read = True
        notification.read_at = now
    db.commit()
    return {"updated_count": len(unread)}


def _get_or_create_setting(db: Session, user_id: UUID) -> UserNotificationSetting:
    setting = db.scalar(
        select(UserNotificationSetting).where(UserNotificationSetting.user_id == user_id)
    )
    if setting is None:
        setting = UserNotificationSetting(user_id=user_id)
        db.add(setting)
        db.flush()
    return setting


def settings_payload(setting: UserNotificationSetting) -> dict:
    return {field: getattr(setting, field) for field in SETTING_FIELDS}


def get_settings(db: Session, *, user: User) -> dict:
    setting = _get_or_create_setting(db, user.id)
    db.commit()
    return settings_payload(setting)


def update_settings(db: Session, *, user: User, changes: dict[str, bool]) -> dict:
    setting = _get_or_create_setting(db, user.id)
    for field, value in changes.items():
        if field in SETTING_FIELDS:
            setattr(setting, field, bool(value))
    db.commit()
    db.refresh(setting)
    return settings_payload(setting)
