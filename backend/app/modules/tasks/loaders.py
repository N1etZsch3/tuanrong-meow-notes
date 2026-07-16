"""SQLAlchemy eager-loading strategies for task queries.

List and detail intentionally use different profiles: the list only loads what the
summary card renders, while the detail loads activities/checkins/photos in full.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.auth.models import User
from app.modules.tasks.models import (
    Task,
    TaskActivityLog,
    TaskCheckin,
    TaskCheckinPhoto,
    TaskExecutionDate,
    TaskPhoto,
)


def task_detail_load_options():
    """Eager-load everything the detail payload renders (activities, checkins, photos)."""
    return (
        selectinload(Task.map_point),
        selectinload(Task.publisher).selectinload(User.profile),
        selectinload(Task.photos).selectinload(TaskPhoto.file_asset),
        selectinload(Task.execution_dates).selectinload(TaskExecutionDate.completed_user),
        selectinload(Task.activities)
        .selectinload(TaskActivityLog.actor)
        .selectinload(User.profile),
        selectinload(Task.checkins).selectinload(TaskCheckin.submitter).selectinload(User.profile),
        selectinload(Task.checkins)
        .selectinload(TaskCheckin.photos)
        .selectinload(TaskCheckinPhoto.file_asset),
        selectinload(Task.checkins)
        .selectinload(TaskCheckin.photos)
        .selectinload(TaskCheckinPhoto.uploader)
        .selectinload(User.profile),
    )


def task_list_load_options():
    """Eager-load only what the list summary renders: cover photo, execution cards, map point."""
    return (
        selectinload(Task.map_point),
        selectinload(Task.photos).selectinload(TaskPhoto.file_asset),
        selectinload(Task.execution_dates).selectinload(TaskExecutionDate.completed_user),
    )


def task_base_statement():
    return select(Task).options(*task_detail_load_options())
