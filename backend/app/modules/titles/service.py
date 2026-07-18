from uuid import UUID

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
    title_payload,
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


def resign_title(db: Session, *, user: User) -> dict:
    profile = db.scalar(
        select(UserProfile)
        .where(UserProfile.user_id == user.id)
        .with_for_update()
    )
    if profile is None or profile.title is None:
        return title_payload(None)
    if profile.title == PRESIDENT:
        raise APIError(
            code=ErrorCode.TITLE_PRESIDENT_TRANSFER_REQUIRED,
            message="会长需要先完成头衔转让",
            status_code=403,
        )

    before_title = profile.title
    profile.title = None
    auth_service.log_admin_operation(
        db,
        admin=user,
        operation_type="user_title_resign",
        target_id=user.id,
        summary=f"成员主动退出头衔 {user.student_no}",
        before_data={"title": before_title},
        after_data={"title": None},
    )
    db.commit()
    return title_payload(None)


def transfer_president(
    db: Session,
    *,
    actor: User,
    successor_id: UUID,
) -> dict:
    ensure_president(actor)
    if actor.id == successor_id:
        raise APIError(
            code=ErrorCode.TITLE_INVALID,
            message="不能将会长头衔转让给自己",
            status_code=422,
        )

    successor = auth_service.get_target_user(db, successor_id)
    profiles = db.scalars(
        select(UserProfile)
        .where(UserProfile.user_id.in_([actor.id, successor.id]))
        .order_by(UserProfile.user_id)
        .with_for_update()
    ).all()
    profiles_by_user_id = {profile.user_id: profile for profile in profiles}
    actor_profile = profiles_by_user_id.get(actor.id)
    successor_profile = profiles_by_user_id.get(successor.id)
    if actor_profile is None or actor_profile.title != PRESIDENT:
        raise APIError(
            code=ErrorCode.TITLE_PRESIDENT_REQUIRED,
            message="仅会长可执行此操作",
            status_code=403,
        )
    if successor_profile is None:
        successor_profile = UserProfile(user_id=successor.id, nickname="")
        db.add(successor_profile)
        db.flush()

    successor_previous_title = successor_profile.title
    successor_previous_role = successor.role
    actor_profile.title = None
    db.flush()
    successor_profile.title = PRESIDENT
    if successor.role not in {"admin", "super_admin"}:
        successor.role = "admin"
        successor.token_version += 1

    auth_service.log_admin_operation(
        db,
        admin=actor,
        operation_type="president_transfer",
        target_id=successor.id,
        summary=f"转让会长头衔给 {successor.student_no}",
        before_data={
            "president_user_id": str(actor.id),
            "successor_title": successor_previous_title,
            "successor_role": successor_previous_role,
        },
        after_data={
            "president_user_id": str(successor.id),
            "successor_title": PRESIDENT,
            "successor_role": successor.role,
        },
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise APIError(
            code=ErrorCode.TITLE_OCCUPIED,
            message="会长头衔已被其他成员使用",
            status_code=409,
        ) from exc

    db.refresh(actor)
    db.refresh(successor)
    return {
        "previous_president": auth_service.admin_user_payload(actor),
        "successor": auth_service.admin_user_payload(successor),
    }


def seed_president(db: Session, *, user: User) -> User:
    existing_profile = db.scalar(
        select(UserProfile)
        .where(UserProfile.title == PRESIDENT)
        .with_for_update()
    )
    if existing_profile is not None and existing_profile.user_id != user.id:
        raise APIError(
            code=ErrorCode.TITLE_OCCUPIED,
            message="系统中已经存在会长",
            status_code=409,
        )

    profile = db.scalar(
        select(UserProfile)
        .where(UserProfile.user_id == user.id)
        .with_for_update()
    )
    if profile is None:
        profile = UserProfile(user_id=user.id, nickname="")
        db.add(profile)
        db.flush()

    before_title = profile.title
    before_role = user.role
    profile.title = PRESIDENT
    if user.role not in {"admin", "super_admin"}:
        user.role = "admin"
        user.token_version += 1
    if before_title != PRESIDENT or before_role != user.role:
        auth_service.log_admin_operation(
            db,
            admin=user,
            operation_type="president_seed",
            target_id=user.id,
            summary=f"初始化会长 {user.student_no}",
            before_data={"title": before_title, "role": before_role},
            after_data={"title": PRESIDENT, "role": user.role},
        )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise APIError(
            code=ErrorCode.TITLE_OCCUPIED,
            message="系统中已经存在会长",
            status_code=409,
        ) from exc
    db.refresh(user)
    return user
