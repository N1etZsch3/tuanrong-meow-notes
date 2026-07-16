"""Read-only task queries: list pagination, detail fetch, SQL filter pushdown.

Nothing in this module writes, flushes, or commits. Lifecycle synchronization is a
separate explicit step (lifecycle_service) that callers run *before* these reads.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Select, case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import APIError
from app.modules.map.models import MapPoint
from app.modules.tasks.constants import TASK_ERROR_NOT_FOUND, TASK_ERROR_UNSUPPORTED_TYPE
from app.modules.tasks.loaders import task_base_statement, task_list_load_options
from app.modules.tasks.models import Task, TaskExecutionDate
from app.modules.tasks.presenters import split_statuses, task_list_item_payload

_FINAL_EXECUTION_DISPLAY_CANCELLED = ("cancelled", "skipped")


def ensure_supported_task_type(task_type: str | None) -> None:
    if task_type and task_type != "feeding":
        raise APIError(
            code=TASK_ERROR_UNSUPPORTED_TYPE,
            message="只支持暑假喂食任务",
            status_code=400,
        )


def get_task_or_raise(db: Session, task_id: UUID, *, include_private: bool = False) -> Task:
    statement = task_base_statement().where(Task.id == task_id, Task.deleted_at.is_(None))
    if not include_private:
        statement = statement.where(Task.is_public.is_(True))
    task = db.scalar(statement)
    if task is None:
        raise APIError(code=TASK_ERROR_NOT_FOUND, message="任务不存在", status_code=404)
    return task


def get_task_by_map_point(db: Session, map_point_id: UUID) -> Task | None:
    return db.scalar(
        task_base_statement().where(
            Task.map_point_id == map_point_id,
            Task.deleted_at.is_(None),
        )
    )


def _execution_display_status_sql(today: date):
    """SQL expression mirroring execution_display_status() for a TaskExecutionDate row."""
    return case(
        (TaskExecutionDate.status == "completed", "completed"),
        (
            TaskExecutionDate.status.in_(_FINAL_EXECUTION_DISPLAY_CANCELLED),
            "cancelled",
        ),
        (TaskExecutionDate.execute_date > today, "not_started"),
        else_="in_progress",
    )


def _execution_child_conditions(
    *,
    execute_date: date | None,
    execute_date_start: date | None,
    execute_date_end: date | None,
    execution_statuses: list[str],
    execution_display_statuses: list[str],
    today: date,
) -> list:
    """Build SQL predicates on TaskExecutionDate matching execution_matches_filters()."""
    conditions = [TaskExecutionDate.deleted_at.is_(None)]
    if execute_date is not None:
        conditions.append(TaskExecutionDate.execute_date == execute_date)
    else:
        if execute_date_start is not None:
            conditions.append(TaskExecutionDate.execute_date >= execute_date_start)
        if execute_date_end is not None:
            conditions.append(TaskExecutionDate.execute_date <= execute_date_end)
    if execution_statuses:
        conditions.append(TaskExecutionDate.status.in_(execution_statuses))
    if execution_display_statuses:
        conditions.append(
            _execution_display_status_sql(today).in_(execution_display_statuses)
        )
    return conditions


def _apply_task_list_filters(
    statement: Select,
    *,
    include_private: bool,
    statuses: list[str],
    keyword: str,
    execute_date: date | None,
    execute_date_start: date | None,
    execute_date_end: date | None,
    execution_statuses: list[str],
    execution_display_statuses: list[str],
    today: date,
) -> Select:
    """Apply every list filter that can be pushed to SQL, including child display status."""
    statement = statement.where(
        Task.deleted_at.is_(None),
        Task.task_type == "feeding",
    )
    if not include_private:
        statement = statement.where(Task.is_public.is_(True))
    if statuses:
        statement = statement.where(Task.status.in_(statuses))
    if keyword:
        statement = statement.join(MapPoint, MapPoint.id == Task.map_point_id).where(
            or_(
                Task.title.contains(keyword),
                MapPoint.location_name.contains(keyword),
                MapPoint.location_detail.contains(keyword),
            )
        )
    child_conditions = _execution_child_conditions(
        execute_date=execute_date,
        execute_date_start=execute_date_start,
        execute_date_end=execute_date_end,
        execution_statuses=execution_statuses,
        execution_display_statuses=execution_display_statuses,
        today=today,
    )
    if len(child_conditions) > 1:
        statement = statement.where(
            exists(
                select(TaskExecutionDate.id).where(
                    TaskExecutionDate.task_id == Task.id,
                    *child_conditions,
                )
            )
        )
    return statement


def list_tasks(
    db: Session,
    *,
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
    today: date,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    statuses = split_statuses(status) if status else []
    normalized_keyword = keyword.strip() if keyword else ""
    query_date = today if only_today else execute_date
    execution_statuses = split_statuses(execution_status)
    execution_display_statuses = split_statuses(execution_display_status)

    filters = dict(
        include_private=include_private,
        statuses=statuses,
        keyword=normalized_keyword,
        execute_date=query_date,
        execute_date_start=execute_date_start,
        execute_date_end=execute_date_end,
        execution_statuses=execution_statuses,
        execution_display_statuses=execution_display_statuses,
        today=today,
    )

    # 第一阶段：数据库内完成 COUNT 与当前页 ID（ORDER BY + OFFSET + LIMIT）。
    total = db.scalar(
        select(func.count()).select_from(
            _apply_task_list_filters(select(Task.id), **filters).subquery()
        )
    )
    start = (page - 1) * page_size
    id_statement = _apply_task_list_filters(select(Task.id), **filters).order_by(
        Task.start_at.asc(),
        Task.published_at.desc(),
        Task.id.desc(),
    )
    page_ids = list(db.scalars(id_statement.offset(start).limit(page_size)).all())

    # 第二阶段：只加载当前页任务及列表所需的轻量关联，并按分页 ID 顺序恢复。
    tasks_by_id: dict[UUID, Task] = {}
    if page_ids:
        loaded = db.scalars(
            select(Task).options(*task_list_load_options()).where(Task.id.in_(page_ids))
        ).all()
        tasks_by_id = {task.id: task for task in loaded}
    paged = [tasks_by_id[task_id] for task_id in page_ids if task_id in tasks_by_id]

    return {
        "items": [
            task_list_item_payload(
                task,
                execute_date=query_date,
                execute_date_start=execute_date_start,
                execute_date_end=execute_date_end,
                execution_status=execution_status,
                execution_display_status=execution_display_status,
                today=today,
            )
            for task in paged
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": start + page_size < total,
    }
