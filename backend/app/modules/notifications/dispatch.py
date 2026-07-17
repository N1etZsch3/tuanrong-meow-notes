"""通知生成与推送（业务事件 → 落库 + WebSocket）。

调用约定：在业务事务内调用 create_notifications 插入通知（不 commit），
由调用方 commit 后再调用 push_created 做 WS 推送，保证「先落库后推送」。
也可直接用 dispatch_notifications 一步完成（内部 commit）。
"""

from __future__ import annotations

from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notifications.constants import channel_for_type
from app.modules.notifications.hub import notification_hub
from app.modules.notifications.models import Notification, UserNotificationSetting
from app.modules.notifications.service import notification_payload


def _recipients_with_channel_enabled(
    db: Session, user_ids: list[UUID], notification_type: str
) -> list[UUID]:
    """按接收者的频道开关过滤；未建开关行的用户视为全开。"""
    if not user_ids:
        return []
    channel_field = f"{channel_for_type(notification_type)}_enabled"
    settings = db.scalars(
        select(UserNotificationSetting).where(UserNotificationSetting.user_id.in_(user_ids))
    ).all()
    disabled = {
        setting.user_id for setting in settings if not getattr(setting, channel_field, True)
    }
    return [user_id for user_id in user_ids if user_id not in disabled]


def create_notifications(
    db: Session,
    *,
    user_ids: list[UUID],
    notification_type: str,
    title: str,
    content: str = "",
    related_type: str | None = None,
    related_id: UUID | None = None,
) -> list[Notification]:
    """为接收者批量插入通知（不 commit）。返回实际插入的通知对象。"""
    recipients = _recipients_with_channel_enabled(db, user_ids, notification_type)
    notifications = [
        Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            content=content,
            related_type=related_type,
            related_id=related_id,
        )
        for user_id in recipients
    ]
    db.add_all(notifications)
    db.flush()
    return notifications


def push_created(notifications: list[Notification]) -> None:
    """commit 之后调用：对在线接收者推送 WS 信封。"""
    for notification in notifications:
        payload = {
            "type": "notification.new",
            "data": jsonable_encoder(notification_payload(notification)),
        }
        notification_hub.notify_threadsafe([notification.user_id], payload)


def dispatch_notifications(
    db: Session,
    *,
    user_ids: list[UUID],
    notification_type: str,
    title: str,
    content: str = "",
    related_type: str | None = None,
    related_id: UUID | None = None,
) -> list[Notification]:
    """插入 + commit + 推送 的一步式入口。"""
    notifications = create_notifications(
        db,
        user_ids=user_ids,
        notification_type=notification_type,
        title=title,
        content=content,
        related_type=related_type,
        related_id=related_id,
    )
    db.commit()
    push_created(notifications)
    return notifications
