"""Explicit task-lifecycle synchronization (the only sanctioned writer on the read path).

State-derivation rules live in execution_state.py; this module owns the transaction:
find due tasks, normalize parent/execution/map-point state, and commit.
Entry points: request facades (before a read), admin write flows, scheduled jobs or
management scripts.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.tasks.execution_state import normalize_task_lifecycle
from app.modules.tasks.models import Task, TaskExecutionDate


def sync_task_lifecycle(
    db: Session,
    task: Task,
    *,
    today: date,
    now: datetime,
) -> bool:
    """Normalize one task's lifecycle and commit if it changed."""
    if normalize_task_lifecycle(task, today=today, now=now):
        db.commit()
        return True
    return False


def sync_due_task_lifecycles(
    db: Session,
    *,
    include_private: bool = True,
    today: date,
    now: datetime,
) -> bool:
    """Normalize lifecycles for all *unsettled* feeding tasks and commit if anything changed.

    A task is a normalization candidate only when it is still active
    (``in_progress``/``completed``) or still has non-final execution dates; fully settled
    tasks are skipped so the scan cost stays proportional to active tasks rather than the
    whole history.
    """
    unsettled = or_(
        Task.status.in_(("in_progress", "completed")),
        exists(
            select(TaskExecutionDate.id).where(
                TaskExecutionDate.task_id == Task.id,
                TaskExecutionDate.deleted_at.is_(None),
                TaskExecutionDate.status.in_(("pending", "missed")),
            )
        ),
    )
    statement = (
        select(Task)
        .options(
            selectinload(Task.map_point),
            selectinload(Task.execution_dates),
        )
        .where(
            Task.deleted_at.is_(None),
            Task.task_type == "feeding",
            unsettled,
        )
    )
    if not include_private:
        statement = statement.where(Task.is_public.is_(True))
    changed = False
    for task in db.scalars(statement):
        changed = normalize_task_lifecycle(task, today=today, now=now) or changed
    if changed:
        db.commit()
    return changed
