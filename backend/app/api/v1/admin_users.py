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
    AdminUpdateRoleRequest,
    AdminUpdateStatusRequest,
)

router = APIRouter(tags=["Admin Users"])


@router.get("", summary="List member accounts")
def list_users(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
    role: str | None = None,
    status: str | None = None,
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
        "role": user.role,
        "status": user.status,
        "must_change_password": user.must_change_password,
    }
    return api_success(data=data, trace_id=request.state.trace_id, message="成员账号创建成功")


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
