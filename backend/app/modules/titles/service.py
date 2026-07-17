from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import APIError, ErrorCode
from app.modules.auth import service as auth_service
from app.modules.auth.models import User, UserProfile
from app.modules.titles.constants import (
    PRESIDENT,
    TITLE_LABELS,
    UNIQUE_TITLE_KEYS,
    normalize_title,
    shield_variant,
)


def ensure_president(actor: User) -> None:
    if actor.profile is None or actor.profile.title != PRESIDENT:
        raise APIError(
            code=ErrorCode.TITLE_PRESIDENT_REQUIRED,
            message="仅会长可执行此操作",
            status_code=403,
        )


def normalize_assignable_title(title: str | None) -> str | None:
    normalized = normalize_title(title)
    if normalized == PRESIDENT or (normalized is not None and normalized not in TITLE_LABELS):
        raise APIError(
            code=ErrorCode.TITLE_INVALID,
            message="头衔无效或不能通过普通授予操作设置",
            status_code=422,
        )
    return normalized


def ensure_title_available(
    db: Session,
    title: str | None,
    *,
    target_user_id=None,
) -> None:
    if title is None:
        return
    holder_user_id = db.scalar(
        select(UserProfile.user_id)
        .where(UserProfile.title == title)
        .with_for_update()
    )
    if holder_user_id is not None and holder_user_id != target_user_id:
        raise APIError(
            code=ErrorCode.TITLE_OCCUPIED,
            message="该头衔已被其他成员使用",
            status_code=409,
        )


def title_catalog(db: Session) -> dict:
    rows = db.execute(
        select(
            UserProfile.title,
            User.id,
            User.student_no,
            UserProfile.nickname,
        )
        .join(User, User.id == UserProfile.user_id)
        .where(
            UserProfile.title.in_(UNIQUE_TITLE_KEYS),
            User.deleted_at.is_(None),
        )
    ).all()
    holders = {
        title: {
            "user_id": user_id,
            "meow_no": student_no,
            "nickname": nickname or "",
        }
        for title, user_id, student_no, nickname in rows
    }
    return {
        "items": [
            {
                "key": title,
                "label": TITLE_LABELS[title],
                "shield": shield_variant(title),
                "is_available": title not in holders,
                "holder": holders.get(title),
            }
            for title in UNIQUE_TITLE_KEYS
        ]
    }


def set_member_title(
    db: Session,
    *,
    actor: User,
    target_user_id,
    title: str | None,
) -> dict:
    ensure_president(actor)
    normalized = normalize_assignable_title(title)
    target = auth_service.get_target_user(db, target_user_id)
    profile = db.scalar(
        select(UserProfile)
        .where(UserProfile.user_id == target.id)
        .with_for_update()
    )
    if profile is None:
        profile = UserProfile(user_id=target.id, nickname="")
        db.add(profile)
        db.flush()
    if profile.title == PRESIDENT:
        raise APIError(
            code=ErrorCode.TITLE_INVALID,
            message="会长头衔只能通过原子转让操作变更",
            status_code=422,
        )
    ensure_title_available(db, normalized, target_user_id=target.id)
    before_title = profile.title
    profile.title = normalized
    auth_service.log_admin_operation(
        db,
        admin=actor,
        operation_type="user_title_update",
        target_id=target.id,
        summary=f"更新成员头衔 {target.student_no}",
        before_data={"title": before_title},
        after_data={"title": normalized},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise APIError(
            code=ErrorCode.TITLE_OCCUPIED,
            message="该头衔已被其他成员使用",
            status_code=409,
        ) from exc
    db.refresh(target)
    return auth_service.admin_user_payload(target)
