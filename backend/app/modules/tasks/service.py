"""Tasks module facade.

This module keeps the public surface that routes (and tests) already use, and owns the
request clock: ``_now()``/``_today()`` are resolved here once per entry point and passed
explicitly into the split services, so tests can keep monkeypatching
``task_service._today`` / ``task_service._now``.

Responsibilities now live in:
- query_service.py      read-only list/detail queries and SQL filter pushdown
- lifecycle_service.py  explicit lifecycle synchronization (the write on the read path)
- command_service.py    admin publish/edit/status/delete transactions
- checkin_service.py    member check-in transactions
- presenters.py         ORM → response payload assembly (no DB access)
- loaders.py            eager-loading strategies for list vs detail
- permissions.py        permission predicates
- constants.py          labels / error codes / timezone
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.tasks import (
    checkin_service,
    command_service,
    lifecycle_service,
    query_service,
)
from app.modules.tasks.constants import (
    EXECUTION_REMOVED_CANCEL_REASON,
    LOCAL_TZ,
    TASK_ERROR_CANCELLED_CANNOT_CHECKIN,
    TASK_ERROR_DUPLICATE_DATE,
    TASK_ERROR_EMPTY_DATES,
    TASK_ERROR_EXECUTION_COMPLETED,
    TASK_ERROR_EXECUTION_NOT_FOUND,
    TASK_ERROR_INVALID_DATES,
    TASK_ERROR_MAP_POINT_INVALID,
    TASK_ERROR_NOT_EXECUTION_DAY,
    TASK_ERROR_NOT_FOUND,
    TASK_ERROR_PARAM,
    TASK_ERROR_PHOTO_INVALID,
    TASK_ERROR_STATUS_CONFLICT,
    TASK_ERROR_UNSUPPORTED_TYPE,
    TASK_STATUS_LABELS,
)
from app.modules.tasks.presenters import task_detail_payload, task_list_item_payload
from app.modules.tasks.query_service import (
    ensure_supported_task_type,
    get_task_by_map_point,
    get_task_or_raise,
)
from app.modules.tasks.schemas import (
    SummerFeedingTaskCreateRequest,
    SummerFeedingTaskUpdateRequest,
    TaskCheckinRequest,
    TaskExecutionStatusUpdateRequest,
    TaskStatusUpdateRequest,
)

__all__ = [
    "EXECUTION_REMOVED_CANCEL_REASON",
    "LOCAL_TZ",
    "TASK_ERROR_CANCELLED_CANNOT_CHECKIN",
    "TASK_ERROR_DUPLICATE_DATE",
    "TASK_ERROR_EMPTY_DATES",
    "TASK_ERROR_EXECUTION_COMPLETED",
    "TASK_ERROR_EXECUTION_NOT_FOUND",
    "TASK_ERROR_INVALID_DATES",
    "TASK_ERROR_MAP_POINT_INVALID",
    "TASK_ERROR_NOT_EXECUTION_DAY",
    "TASK_ERROR_NOT_FOUND",
    "TASK_ERROR_PARAM",
    "TASK_ERROR_PHOTO_INVALID",
    "TASK_ERROR_STATUS_CONFLICT",
    "TASK_ERROR_UNSUPPORTED_TYPE",
    "TASK_STATUS_LABELS",
    "checkin_task",
    "delete_task_checkin_photo",
    "get_task_by_map_point",
    "get_task_detail",
    "get_task_or_raise",
    "list_tasks",
    "publish_summer_feeding_task",
    "soft_delete_task",
    "sync_due_task_lifecycles",
    "sync_task_lifecycle",
    "task_detail_payload",
    "task_list_item_payload",
    "update_summer_feeding_task",
    "update_task_execution_status",
    "update_task_status",
]


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _today() -> date:
    return _now().astimezone(LOCAL_TZ).date()


def sync_due_task_lifecycles(
    db: Session,
    *,
    include_private: bool = True,
    today: date | None = None,
) -> bool:
    """Explicit lifecycle sync entry point (cron / scripts / request facades)."""
    return lifecycle_service.sync_due_task_lifecycles(
        db,
        include_private=include_private,
        today=today or _today(),
        now=_now(),
    )


def sync_task_lifecycle(
    db: Session,
    task,
    *,
    today: date | None = None,
) -> bool:
    """Explicit single-task lifecycle sync; commits when the task changed."""
    return lifecycle_service.sync_task_lifecycle(
        db,
        task,
        today=today or _today(),
        now=_now(),
    )


def list_tasks(
    db: Session,
    *,
    task_type: str | None = "feeding",
    status: str | None = "in_progress",
    keyword: str | None = None,
    execute_date: date | None = None,
    execute_date_start: date | None = None,
    execute_date_end: date | None = None,
    execution_status: str | None = None,
    execution_display_status: str | None = None,
    only_today: bool = False,
    page: int = 1,
    page_size: int = 20,
    include_private: bool = False,
) -> dict:
    ensure_supported_task_type(task_type)
    today = _today()
    # 显式生命周期同步（写）：在只读分页查询之前把到期任务状态归一，使 SQL 过滤/计数准确。
    lifecycle_service.sync_due_task_lifecycles(
        db,
        include_private=include_private,
        today=today,
        now=_now(),
    )
    return query_service.list_tasks(
        db,
        status=status,
        keyword=keyword,
        execute_date=execute_date,
        execute_date_start=execute_date_start,
        execute_date_end=execute_date_end,
        execution_status=execution_status,
        execution_display_status=execution_display_status,
        only_today=only_today,
        page=page,
        page_size=page_size,
        include_private=include_private,
        today=today,
    )


def get_task_detail(
    db: Session,
    *,
    task_id: UUID,
    current_date: date | None = None,
    execution_date_id: UUID | None = None,
    include_private: bool = False,
    activity_limit: int = 20,
    can_admin_edit: bool = False,
    viewer: User | None = None,
) -> dict:
    today = current_date or _today()
    task = get_task_or_raise(db, task_id, include_private=include_private)
    # 显式生命周期同步（写）先行，随后 task_detail_payload 只做只读组装。
    if lifecycle_service.sync_task_lifecycle(db, task, today=today, now=_now()):
        task = get_task_or_raise(db, task_id, include_private=include_private)
    return task_detail_payload(
        task,
        current_date=today,
        execution_date_id=execution_date_id,
        activity_limit=activity_limit,
        can_admin_edit=can_admin_edit,
        viewer=viewer,
    )


def publish_summer_feeding_task(
    db: Session,
    *,
    admin: User,
    payload: SummerFeedingTaskCreateRequest,
) -> dict:
    return command_service.publish_summer_feeding_task(
        db,
        admin=admin,
        payload=payload,
        now=_now(),
    )


def update_summer_feeding_task(
    db: Session,
    *,
    task_id: UUID,
    admin: User,
    payload: SummerFeedingTaskUpdateRequest,
) -> dict:
    return command_service.update_summer_feeding_task(
        db,
        task_id=task_id,
        admin=admin,
        payload=payload,
        today=_today(),
        now=_now(),
    )


def update_task_execution_status(
    db: Session,
    *,
    task_id: UUID,
    execution_date_id: UUID,
    admin: User,
    payload: TaskExecutionStatusUpdateRequest,
) -> dict:
    return command_service.update_task_execution_status(
        db,
        task_id=task_id,
        execution_date_id=execution_date_id,
        admin=admin,
        payload=payload,
        today=_today(),
        now=_now(),
    )


def update_task_status(
    db: Session,
    *,
    task_id: UUID,
    admin: User,
    payload: TaskStatusUpdateRequest,
) -> dict:
    return command_service.update_task_status(
        db,
        task_id=task_id,
        admin=admin,
        payload=payload,
        now=_now(),
    )


def soft_delete_task(
    db: Session,
    *,
    task_id: UUID,
    admin: User,
) -> dict:
    return command_service.soft_delete_task(db, task_id=task_id, admin=admin, now=_now())


def checkin_task(
    db: Session,
    *,
    task_id: UUID,
    user: User,
    payload: TaskCheckinRequest,
) -> dict:
    return checkin_service.checkin_task(
        db,
        task_id=task_id,
        user=user,
        payload=payload,
        today=_today(),
        now=_now(),
    )


def delete_task_checkin_photo(
    db: Session,
    *,
    task_id: UUID,
    photo_id: UUID,
    user: User,
) -> dict:
    return checkin_service.delete_task_checkin_photo(
        db,
        task_id=task_id,
        photo_id=photo_id,
        user=user,
        now=_now(),
    )
