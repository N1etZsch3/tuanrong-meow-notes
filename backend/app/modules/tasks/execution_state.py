from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from app.modules.tasks.models import Task, TaskExecutionDate

LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def local_today(now: datetime) -> date:
    return now.astimezone(LOCAL_TZ).date()

DISPLAY_STATUS_LABELS = {
    "not_started": "未开始",
    "in_progress": "进行中",
    "completed": "已完成",
    "cancelled": "已取消",
}

AUTO_ARCHIVE_AFTER_DAYS = 3

FINAL_EXECUTION_STATUSES = {"completed", "cancelled", "skipped"}

AUTO_ARCHIVE_CANCEL_REASON = "父任务已归档，未完成子任务自动取消"
PARENT_CANCEL_REASON = "父任务已取消，未完成子任务自动取消"
PARENT_COMPLETE_CANCEL_REASON = "父任务已完成，未完成子任务自动取消"


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


def should_auto_complete_task(execution_dates: list[TaskExecutionDate]) -> bool:
    active_dates = active_execution_dates(execution_dates)
    if not active_dates:
        return False
    return all(item.status in FINAL_EXECUTION_STATUSES for item in active_dates)


def has_unfinished_executions(execution_dates: list[TaskExecutionDate]) -> bool:
    return any(
        item.status not in FINAL_EXECUTION_STATUSES
        for item in active_execution_dates(execution_dates)
    )


def _hide_task_map_point(task: Task, *, now: datetime) -> None:
    if task.map_point is None or task.map_point.deleted_at is not None:
        return
    task.map_point.visibility = "hidden"
    task.map_point.status = "active"
    task.map_point.updated_at = now


def normalize_task_lifecycle(task: Task, *, today: date, now: datetime) -> bool:
    """统一父子任务生命周期：子任务状态归一 → 父任务前向/反向派生 → 日期归档。

    规则：
    - 子任务全部为最终态（完成/取消/跳过）时，父任务自动置为“已完成”。
    - 父任务“已完成”但又出现未完成子任务（如管理员补充执行日）时，回到“进行中”。
    - 归档保持原逻辑：最后一个执行日 + 3 天后自动归档并隐藏地图点。
    """
    changed = normalize_execution_date_states(
        task.execution_dates,
        today=today,
        now=now,
    )
    if task.status == "in_progress" and should_auto_complete_task(task.execution_dates):
        task.status = "completed"
        task.completed_at = now
        task.cancelled_at = None
        task.updated_at = now
        changed = True
    elif task.status == "completed" and has_unfinished_executions(task.execution_dates):
        task.status = "in_progress"
        task.completed_at = None
        task.updated_at = now
        changed = True
    if task.status in {"in_progress", "completed"} and should_auto_archive_task(
        task.execution_dates,
        today=today,
    ):
        task.status = "archived"
        task.completed_at = task.completed_at or now
        task.cancelled_at = None
        task.updated_at = now
        _hide_task_map_point(task, now=now)
        cancel_unfinished_execution_dates(
            task.execution_dates,
            now=now,
            reason=AUTO_ARCHIVE_CANCEL_REASON,
        )
        changed = True
    if task.status in {"cancelled", "archived"}:
        changed = (
            cancel_unfinished_execution_dates(
                task.execution_dates,
                now=now,
                reason=(
                    AUTO_ARCHIVE_CANCEL_REASON
                    if task.status == "archived"
                    else PARENT_CANCEL_REASON
                ),
            )
            or changed
        )
    return changed


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
