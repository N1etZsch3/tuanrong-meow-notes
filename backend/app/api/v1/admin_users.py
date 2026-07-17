from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.dependencies import require_admin
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    AdminCreateUserRequest,
    AdminResetPasswordRequest,
    AdminRestoreUserRequest,
    AdminUpdateRoleRequest,
    AdminUpdateStatusRequest,
    AdminUpdateUserRequest,
)
from app.modules.titles import service as titles_service
from app.modules.titles.dependencies import require_president
from app.modules.titles.schemas import SetMemberTitleRequest

router = APIRouter(tags=["Admin Users"])


@router.patch("/{user_id}/title", summary="Grant or revoke a member title")
def update_user_title(
    user_id: UUID,
    payload: SetMemberTitleRequest,
    request: Request,
    db: Session = Depends(get_db),
    president: User = Depends(require_president),
):
    data = titles_service.set_member_title(
        db,
        actor=president,
        target_user_id=user_id,
        title=payload.title,
    )
    return api_success(data=data, trace_id=request.state.trace_id, message="成员头衔已更新")


@router.get("", summary="List member accounts")
def list_users(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
    role: str | None = None,
    status: str | None = None,
    department: str | None = None,
    sort_by: str | None = None,
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.list_users(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        role=role,
        status=status,
        department=department,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("", summary="Create member account")
def create_user(
    payload: AdminCreateUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = service.create_member_account(db, admin, payload)
    data = {
        "id": user.id,
        "student_no": user.student_no,
        "meow_no": user.student_no,
        "role": user.role,
        "status": user.status,
        "must_change_password": user.must_change_password,
    }
    return api_success(data=data, trace_id=request.state.trace_id, message="成员账号创建成功")


@router.get("/{user_id}", summary="Get member account detail")
def get_user_detail(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.get_user_detail(db, user_id=user_id)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/{user_id}", summary="Update member account detail")
def update_user_detail(
    user_id: UUID,
    payload: AdminUpdateUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.update_user_detail(db, admin=admin, user_id=user_id, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id, message="成员资料已更新")


@router.patch("/{user_id}/password", summary="Reset member password")
def reset_password(
    user_id: UUID,
    payload: AdminResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = service.reset_user_password(db, admin=admin, user_id=user_id, payload=payload)
    return api_success(
        data={"user_id": user.id, "must_change_password": user.must_change_password},
        trace_id=request.state.trace_id,
        message="密码已重置",
    )


@router.patch("/{user_id}/reset-password", summary="Reset member password")
def reset_password_alias(
    user_id: UUID,
    payload: AdminResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return reset_password(user_id=user_id, payload=payload, request=request, db=db, admin=admin)


@router.delete("/{user_id}", summary="Soft delete member account")
def delete_user(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = service.soft_delete_user(db, admin=admin, user_id=user_id)
    return api_success(
        data={"user_id": user.id, "status": user.status, "deleted_at": user.deleted_at},
        trace_id=request.state.trace_id,
        message="成员已退出",
    )


@router.post("/{user_id}/restore", summary="Restore a soft-deleted member account")
def restore_user(
    user_id: UUID,
    payload: AdminRestoreUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = service.restore_user(
        db,
        admin=admin,
        user_id=user_id,
        payload=payload,
    )
    return api_success(
        data={
            "id": user.id,
            "student_no": user.student_no,
            "meow_no": user.student_no,
            "nickname": user.profile.nickname if user.profile else "",
            "role": user.role,
            "status": user.status,
            "must_change_password": user.must_change_password,
            "wechat_bound": bool(user.wechat_openid),
        },
        trace_id=request.state.trace_id,
        message="成员账号已重新启用",
    )


@router.delete("/{user_id}/wechat-binding", summary="Clear member WeChat binding")
def clear_wechat_binding(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = service.clear_user_wechat_binding(db, admin=admin, user_id=user_id)
    return api_success(
        data={"user_id": user.id, "wechat_bound": False, "token_version": user.token_version},
        trace_id=request.state.trace_id,
        message="微信绑定已清除",
    )


@router.patch("/{user_id}/status", summary="Update member status")
def update_status(
    user_id: UUID,
    payload: AdminUpdateStatusRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = service.update_user_status(db, admin=admin, user_id=user_id, payload=payload)
    return api_success(
        data={"user_id": user.id, "status": user.status},
        trace_id=request.state.trace_id,
        message="账号状态已更新",
    )


@router.patch("/{user_id}/role", summary="Update member role")
def update_role(
    user_id: UUID,
    payload: AdminUpdateRoleRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = service.update_user_role(db, admin=admin, user_id=user_id, payload=payload)
    return api_success(
        data={"user_id": user.id, "role": user.role},
        trace_id=request.state.trace_id,
        message="角色已更新",
    )
