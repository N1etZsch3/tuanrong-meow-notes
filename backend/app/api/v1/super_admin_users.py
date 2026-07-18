from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import APIError, ErrorCode
from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.dependencies import require_super_admin
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    AdminCreateUserRequest,
    AdminResetPasswordRequest,
    AdminRestoreUserRequest,
    AdminUpdateRoleRequest,
    AdminUpdateStatusRequest,
    AdminUpdateUserRequest,
)

router = APIRouter(tags=["Super Admin Users"])


@router.post("/admins", summary="Create an administrator account")
def create_admin(
    payload: AdminCreateUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    if payload.role != "admin":
        raise APIError(
            code=ErrorCode.PARAM_ERROR,
            message="超级管理员接口只能创建管理员账号",
            status_code=400,
        )
    user = service.create_member_account(
        db,
        super_admin,
        payload,
        allowed_roles={"admin"},
    )
    return api_success(
        data={
            "id": user.id,
            "student_no": user.student_no,
            "meow_no": user.student_no,
            "role": user.role,
            "status": user.status,
            "must_change_password": user.must_change_password,
        },
        trace_id=request.state.trace_id,
        message="管理员账号创建成功",
    )


@router.patch("/{user_id}", summary="Update an administrator account")
def update_admin_detail(
    user_id: UUID,
    payload: AdminUpdateUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    data = service.update_user_detail(
        db,
        admin=super_admin,
        user_id=user_id,
        payload=payload,
        allow_admin_target=True,
        allowed_roles=service.VALID_ROLES,
    )
    return api_success(data=data, trace_id=request.state.trace_id, message="管理员资料已更新")


@router.patch("/{user_id}/password", summary="Reset an administrator password")
@router.patch("/{user_id}/reset-password", summary="Reset an administrator password")
def reset_admin_password(
    user_id: UUID,
    payload: AdminResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    user = service.reset_user_password(
        db,
        admin=super_admin,
        user_id=user_id,
        payload=payload,
        allow_admin_target=True,
    )
    return api_success(
        data={"user_id": user.id, "must_change_password": user.must_change_password},
        trace_id=request.state.trace_id,
        message="管理员密码已重置",
    )


@router.delete("/{user_id}", summary="Soft delete an administrator account")
def delete_admin(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    user = service.soft_delete_user(
        db,
        admin=super_admin,
        user_id=user_id,
        allow_admin_target=True,
    )
    return api_success(
        data={"user_id": user.id, "status": user.status, "deleted_at": user.deleted_at},
        trace_id=request.state.trace_id,
        message="管理员已退出",
    )


@router.post("/{user_id}/restore", summary="Restore an administrator account")
def restore_admin(
    user_id: UUID,
    payload: AdminRestoreUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    user = service.restore_user(
        db,
        admin=super_admin,
        user_id=user_id,
        payload=payload,
        allow_admin_target=True,
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
        message="管理员账号已重新启用",
    )


@router.delete("/{user_id}/wechat-binding", summary="Clear administrator WeChat binding")
def clear_admin_wechat_binding(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    user = service.clear_user_wechat_binding(
        db,
        admin=super_admin,
        user_id=user_id,
        allow_admin_target=True,
    )
    return api_success(
        data={"user_id": user.id, "wechat_bound": False, "token_version": user.token_version},
        trace_id=request.state.trace_id,
        message="管理员微信绑定已清除",
    )


@router.patch("/{user_id}/status", summary="Update administrator status")
def update_admin_status(
    user_id: UUID,
    payload: AdminUpdateStatusRequest,
    request: Request,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    user = service.update_user_status(
        db,
        admin=super_admin,
        user_id=user_id,
        payload=payload,
        allow_admin_target=True,
    )
    return api_success(
        data={"user_id": user.id, "status": user.status},
        trace_id=request.state.trace_id,
        message="管理员账号状态已更新",
    )


@router.patch("/{user_id}/role", summary="Assign or revoke administrator role")
def update_admin_role(
    user_id: UUID,
    payload: AdminUpdateRoleRequest,
    request: Request,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    user = service.update_user_role(
        db,
        admin=super_admin,
        user_id=user_id,
        payload=payload,
        allow_admin_target=True,
        allowed_roles=service.VALID_ROLES,
    )
    return api_success(
        data={"user_id": user.id, "role": user.role},
        trace_id=request.state.trace_id,
        message="管理员身份已更新",
    )
