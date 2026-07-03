from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.auth.models import User
from app.modules.tasks import service
from app.modules.tasks.schemas import (
    SummerFeedingTaskCreateRequest,
    SummerFeedingTaskUpdateRequest,
    TaskStatusUpdateRequest,
)

router = APIRouter(tags=["Admin Tasks"])


@router.get("", summary="Admin list summer feeding tasks")
def list_admin_tasks(
    request: Request,
    task_type: str | None = "feeding",
    status: str | None = None,
    keyword: str | None = None,
    execute_date: date | None = None,
    execute_date_start: date | None = None,
    execute_date_end: date | None = None,
    execution_status: str | None = None,
    execution_display_status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.list_tasks(
        db,
        task_type=task_type,
        status=status,
        keyword=keyword,
        execute_date=execute_date,
        execute_date_start=execute_date_start,
        execute_date_end=execute_date_end,
        execution_status=execution_status,
        execution_display_status=execution_display_status,
        page=page,
        page_size=page_size,
        include_private=True,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/{task_id}", summary="Admin get editable summer feeding task detail")
def get_admin_task_detail(
    task_id: UUID,
    request: Request,
    current_date: date | None = None,
    execution_date_id: UUID | None = None,
    activity_limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.get_task_detail(
        db,
        task_id=task_id,
        current_date=current_date,
        execution_date_id=execution_date_id,
        include_private=True,
        activity_limit=activity_limit,
        can_admin_edit=True,
        viewer=admin,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/summer-feeding", summary="Publish a summer feeding task")
def publish_summer_feeding_task(
    payload: SummerFeedingTaskCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.publish_summer_feeding_task(db, admin=admin, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id, message="喂食任务已发布")


@router.patch("/{task_id}", summary="Update a summer feeding task")
def update_summer_feeding_task(
    task_id: UUID,
    payload: SummerFeedingTaskUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.update_summer_feeding_task(db, task_id=task_id, admin=admin, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id, message="任务已更新")


@router.patch("/{task_id}/status", summary="Update summer feeding task status")
def update_task_status(
    task_id: UUID,
    payload: TaskStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.update_task_status(db, task_id=task_id, admin=admin, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id, message="任务状态已更新")


@router.delete("/{task_id}", summary="Soft delete a summer feeding task")
def soft_delete_task(
    task_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.soft_delete_task(db, task_id=task_id, admin=admin)
    return api_success(data=data, trace_id=request.state.trace_id, message="任务已删除")
