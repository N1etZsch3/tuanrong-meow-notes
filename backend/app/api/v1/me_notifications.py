from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.notifications import service

router = APIRouter(tags=["Notifications"])


class NotificationSettingsRequest(BaseModel):
    task_enabled: bool | None = None
    feeding_enabled: bool | None = None
    medicine_enabled: bool | None = None
    supply_enabled: bool | None = None
    member_enabled: bool | None = None
    cat_enabled: bool | None = None
    announcement_enabled: bool | None = None


@router.get("/notifications", summary="List my notifications")
def notification_list(
    request: Request,
    is_read: bool | None = Query(default=None),
    notification_type: str | None = Query(default=None, max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = service.list_notifications(
        db,
        user=current_user,
        is_read=is_read,
        notification_type=notification_type,
        page=page,
        page_size=page_size,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/notifications/unread-count", summary="Get unread notification count")
def notification_unread_count(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = {"unread_count": service.unread_count(db, user=current_user)}
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/notifications/read-all", summary="Mark all notifications read")
def notification_read_all(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = service.mark_all_read(db, user=current_user)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/notifications/{notification_id}/read", summary="Mark one notification read")
def notification_read(
    notification_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = service.mark_read(db, user=current_user, notification_id=notification_id)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/notification-settings", summary="Get notification settings")
def notification_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = service.get_settings(db, user=current_user)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/notification-settings", summary="Update notification settings")
def notification_settings_update(
    payload: NotificationSettingsRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    changes = {
        field: value
        for field, value in payload.model_dump(exclude_unset=True).items()
        if value is not None
    }
    data = service.update_settings(db, user=current_user, changes=changes)
    return api_success(data=data, trace_id=request.state.trace_id)
