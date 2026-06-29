from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.tasks import service
from app.modules.tasks.schemas import TaskCheckinRequest

router = APIRouter(tags=["Tasks"])


@router.get("", summary="List summer feeding tasks")
def list_tasks(
    request: Request,
    task_type: str | None = "feeding",
    status: str | None = "in_progress",
    keyword: str | None = None,
    execute_date: date | None = None,
    only_today: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.list_tasks(
        db,
        task_type=task_type,
        status=status,
        keyword=keyword,
        execute_date=execute_date,
        only_today=only_today,
        page=page,
        page_size=page_size,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/{task_id}", summary="Get summer feeding task detail")
def task_detail(
    task_id: UUID,
    request: Request,
    current_date: date | None = None,
    activity_limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.get_task_detail(
        db,
        task_id=task_id,
        current_date=current_date,
        activity_limit=activity_limit,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{task_id}/checkins", summary="Complete a summer feeding execution date")
def checkin_task(
    task_id: UUID,
    payload: TaskCheckinRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.checkin_task(db, task_id=task_id, user=current_user, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id, message="投喂已完成")
