from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import UUID

from app.modules.tasks.models import TaskExecutionDate

DISPLAY_STATUS_LABELS = {
    "not_started": "未开始",
    "in_progress": "进行中",
    "completed": "已完成",
    "cancelled": "已取消",
}

AUTO_ARCHIVE_AFTER_DAYS = 3


def active_execution_dates(
    execution_dates: list[TaskExecutionDate],
) -> list[TaskExecutionDate]:
    return sorted(
        (item for item in execution_dates if item.deleted_at is None),
        key=lambda item: item.execute_date,
    )


def normalize_execution_date_states(
    execution_dates: list[TaskExecutionDate],
    *,
    today: date,
    now: datetime,
) -> bool:
    changed = False
    active_dates = active_execution_dates(execution_dates)
    for index, execution in enumerate(active_dates[:-1]):
        next_execution = active_dates[index + 1]
        if execution.status in {"pending", "missed"} and next_execution.execute_date <= today:
            execution.status = "cancelled"
            execution.cancelled_at = now
            execution.cancel_reason = "下一次子任务已开启，上一子任务自动取消"
            execution.remark = execution.remark or execution.cancel_reason
            changed = True
    return changed


def cancel_unfinished_execution_dates(
    execution_dates: list[TaskExecutionDate],
    *,
    now: datetime,
    reason: str,
    cancelled_by: UUID | None = None,
) -> bool:
    changed = False
    for execution in active_execution_dates(execution_dates):
        if execution.status not in {"pending", "missed"}:
            continue
        execution.status = "cancelled"
        execution.cancelled_at = now
        execution.cancelled_by = cancelled_by
        execution.cancel_reason = reason
        execution.remark = execution.remark or reason
        changed = True
    return changed


def should_auto_archive_task(
    execution_dates: list[TaskExecutionDate],
    *,
    today: date,
) -> bool:
    active_dates = active_execution_dates(execution_dates)
    if not active_dates:
        return False
    archive_date = active_dates[-1].execute_date + timedelta(days=AUTO_ARCHIVE_AFTER_DAYS)
    return today >= archive_date


def execution_display_status(
    execution_date: TaskExecutionDate,
    *,
    today: date,
) -> str:
    if execution_date.status == "completed":
        return "completed"
    if execution_date.status in {"cancelled", "skipped"}:
        return "cancelled"
    if execution_date.execute_date > today:
        return "not_started"
    return "in_progress"


def execution_display_status_label(status: str) -> str:
    return DISPLAY_STATUS_LABELS.get(status, status)


def active_execution(
    execution_dates: list[TaskExecutionDate],
    *,
    today: date,
) -> TaskExecutionDate | None:
    active_dates = active_execution_dates(execution_dates)
    if not active_dates:
        return None
    exact = next((item for item in active_dates if item.execute_date == today), None)
    if exact:
        return exact
    past_or_today = [item for item in active_dates if item.execute_date <= today]
    if past_or_today:
        return past_or_today[-1]
    return active_dates[0]
