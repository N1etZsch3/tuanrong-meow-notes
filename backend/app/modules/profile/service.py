from sqlalchemy.orm import Session

from app.core.errors import APIError, ErrorCode
from app.modules.auth.departments_service import (
    set_user_departments,
    user_department_names,
)
from app.modules.auth.models import User, UserProfile
from app.modules.auth.service import clean_initial_display_text, clean_initial_text, now_utc
from app.modules.profile.schemas import CompleteProfileRequest, UpdateProfileRequest
from app.modules.titles.constants import title_payload


def profile_payload(user: User) -> dict:
    profile = user.profile
    departments = user_department_names(user)
    return {
        "user_id": user.id,
        "student_no": user.student_no,
        "meow_no": user.student_no,
        "role": user.role,
        "nickname": clean_initial_display_text(profile.nickname if profile else None),
        "avatar_url": profile.avatar_url if profile else None,
        "avatar_review_asset_id": profile.avatar_review_asset_id if profile else None,
        "avatar_review_status": profile.avatar_review_status if profile else "idle",
        "department": departments[0] if departments else clean_initial_text(
            profile.department if profile else None
        ),
        "departments": departments,
        **title_payload(profile.title if profile else None),
        "contact_info": clean_initial_text(profile.contact_info if profile else None),
        "profile_completed": bool(profile and profile.profile_completed),
        "profile_completed_at": profile.profile_completed_at if profile else None,
    }


def complete_profile(db: Session, user: User, payload: CompleteProfileRequest) -> dict:
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id, nickname=payload.nickname)
        db.add(profile)

    if payload.avatar_url is not None and payload.avatar_url != profile.avatar_url:
        raise APIError(
            code=ErrorCode.FILE_SECURITY_REJECTED,
            message="请通过头像上传功能提交图片审核",
            status_code=422,
        )
    profile.nickname = payload.nickname
    set_user_departments(db, user, list(payload.resolved_departments()))
    profile.contact_info = payload.contact_info
    profile.profile_completed = True
    profile.profile_completed_at = now_utc()
    db.commit()
    db.refresh(profile)
    return {
        "profile_completed": True,
        "next_action": "enter_app",
    }


def update_profile(db: Session, user: User, payload: UpdateProfileRequest) -> dict:
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id, nickname="")
        db.add(profile)

    fields_set = payload.model_fields_set
    if "nickname" in fields_set and payload.nickname is not None:
        profile.nickname = payload.nickname.strip()
    if "avatar_url" in fields_set:
        if payload.avatar_url != profile.avatar_url:
            raise APIError(
                code=ErrorCode.FILE_SECURITY_REJECTED,
                message="请通过头像上传功能提交图片审核",
                status_code=422,
            )
    # departments 优先；仅传旧单值 department 时按单元素处理（兼容旧客户端）。
    if "departments" in fields_set and payload.departments is not None:
        set_user_departments(db, user, list(payload.departments))
    elif "department" in fields_set:
        set_user_departments(
            db, user, [payload.department] if payload.department else []
        )
    if "contact_info" in fields_set:
        profile.contact_info = payload.contact_info

    db.commit()
    db.refresh(profile)
    return profile_payload(user)
