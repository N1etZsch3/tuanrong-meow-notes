"""Task check-in flows: create a check-in with photos, delete a check-in photo.

Each public function owns one transaction. Lifecycle sync before a check-in is the
explicit lifecycle_service step; the closing normalization runs inside the check-in
transaction so parent status and the new completion commit atomically.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import APIError, ErrorCode
from app.modules.auth.models import User
from app.modules.files.models import FileAsset
from app.modules.tasks.command_service import resolve_uploaded_file_urls
from app.modules.tasks.constants import (
    LOCAL_TZ,
    TASK_ERROR_CANCELLED_CANNOT_CHECKIN,
    TASK_ERROR_EXECUTION_COMPLETED,
    TASK_ERROR_EXECUTION_NOT_FOUND,
    TASK_ERROR_NOT_EXECUTION_DAY,
    TASK_ERROR_STATUS_CONFLICT,
)
from app.modules.tasks.execution_state import normalize_task_lifecycle
from app.modules.tasks.lifecycle_service import sync_task_lifecycle
from app.modules.tasks.models import (
    TaskActivityLog,
    TaskCheckin,
    TaskCheckinPhoto,
    TaskExecutionDate,
)
from app.modules.tasks.permissions import can_delete_checkin_photo
from app.modules.tasks.presenters import checkin_photo_payload, user_payload
from app.modules.tasks.query_service import get_task_or_raise
from app.modules.tasks.schemas import TaskCheckinRequest, UploadedFileRef


def _local_date_text(value: datetime) -> str:
    return value.astimezone(LOCAL_TZ).date().isoformat()


def _checkin_photo(
    db: Session,
    *,
    task_id: UUID,
    checkin_id: UUID,
    photo: UploadedFileRef,
    uploaded_by: User,
    sort_order: int,
) -> TaskCheckinPhoto:
    file_id, file_url, thumbnail_url = resolve_uploaded_file_urls(
        db,
        photo,
        uploaded_by=uploaded_by,
        allowed_usage_types={"task_checkin_photo"},
    )
    checkin_photo = TaskCheckinPhoto(
        checkin_id=checkin_id,
        task_id=task_id,
        file_id=file_id,
        file_url=file_url,
        thumbnail_url=thumbnail_url,
        sort_order=sort_order,
        uploaded_by=uploaded_by.id,
    )
    checkin_photo.uploader = uploaded_by
    db.add(checkin_photo)
    return checkin_photo


def checkin_task(
    db: Session,
    *,
    task_id: UUID,
    user: User,
    payload: TaskCheckinRequest,
    today: date,
    now: datetime,
) -> dict:
    task = get_task_or_raise(db, task_id)
    if sync_task_lifecycle(db, task, today=today, now=now):
        task = get_task_or_raise(db, task_id)
    if task.status == "cancelled":
        raise APIError(
            code=TASK_ERROR_CANCELLED_CANNOT_CHECKIN,
            message="已取消的任务不能完成投喂",
            status_code=409,
        )
    if task.status != "in_progress":
        raise APIError(
            code=TASK_ERROR_STATUS_CONFLICT,
            message="任务状态不允许完成",
            status_code=409,
        )

    execute_date = payload.execute_date or today
    if execute_date > today:
        raise APIError(
            code=TASK_ERROR_NOT_EXECUTION_DAY,
            message="未到任务日期",
            status_code=400,
        )
    execution = db.scalar(
        select(TaskExecutionDate)
        .where(
            TaskExecutionDate.task_id == task_id,
            TaskExecutionDate.execute_date == execute_date,
            TaskExecutionDate.deleted_at.is_(None),
        )
        .with_for_update()
    )
    if execution is None:
        raise APIError(
            code=TASK_ERROR_NOT_EXECUTION_DAY,
            message="今天不是该任务执行日",
            status_code=400,
        )
    if execution.status == "completed":
        raise APIError(
            code=TASK_ERROR_EXECUTION_COMPLETED,
            message="该执行日期已完成",
            status_code=409,
        )
    if execution.status not in {"pending", "missed"}:
        raise APIError(
            code=TASK_ERROR_EXECUTION_NOT_FOUND,
            message="执行日期不存在",
            status_code=404,
        )

    checkin = TaskCheckin(
        task_id=task.id,
        task_execution_date_id=execution.id,
        execute_date=execute_date,
        submitter_id=user.id,
        is_completed=payload.is_completed,
        process_result=payload.process_result,
        remark=payload.remark,
        review_status="no_review",
        checkin_type="feeding",
        checkin_lng=Decimal(str(payload.checkin_lng)) if payload.checkin_lng is not None else None,
        checkin_lat=Decimal(str(payload.checkin_lat)) if payload.checkin_lat is not None else None,
        submitted_at=now,
    )
    db.add(checkin)
    db.flush()
    checkin_photos = []
    for index, photo in enumerate(payload.photos):
        checkin_photos.append(
            _checkin_photo(
                db,
                task_id=task.id,
                checkin_id=checkin.id,
                photo=photo,
                uploaded_by=user,
                sort_order=index,
            )
        )
    db.flush()

    execution.status = "completed"
    execution.completed_by = user.id
    execution.completed_at = now
    execution.checkin_id = checkin.id
    execution.remark = payload.remark

    ordered_dates = sorted(
        [item for item in task.execution_dates if item.deleted_at is None],
        key=lambda item: item.execute_date,
    )
    sequence = next(
        (index + 1 for index, item in enumerate(ordered_dates) if item.id == execution.id),
        1,
    )
    nickname = user.profile.nickname if user.profile else user.student_no
    completed_date_text = _local_date_text(now)
    db.add(
        TaskActivityLog(
            task_id=task.id,
            task_execution_date_id=execution.id,
            activity_type="execution_completed",
            title=f"第{sequence}次任务完成",
            content=f"{nickname} 于 {completed_date_text} 完成投喂",
            actor_id=user.id,
            activity_metadata={
                "execute_date": execute_date.isoformat(),
                "completed_at": now.isoformat(),
                "checkin_id": str(checkin.id),
            },
            created_at=now,
        )
    )
    normalize_task_lifecycle(task, today=today, now=now)
    db.commit()
    return {
        "execution_date_id": execution.id,
        "execute_date": execute_date.isoformat(),
        "status": execution.status,
        "checkin": {
            "checkin_id": checkin.id,
            "task_id": task.id,
            "task_execution_date_id": execution.id,
            "execute_date": execute_date.isoformat(),
            "submitter": user_payload(user),
            "is_completed": checkin.is_completed,
            "process_result": checkin.process_result,
            "remark": checkin.remark,
            "submitted_at": checkin.submitted_at,
            "photos": [
                checkin_photo_payload(photo, user)
                for photo in sorted(checkin_photos, key=lambda item: item.sort_order)
            ],
        },
    }


def delete_task_checkin_photo(
    db: Session,
    *,
    task_id: UUID,
    photo_id: UUID,
    user: User,
    now: datetime,
) -> dict:
    photo = db.scalar(
        select(TaskCheckinPhoto)
        .options(selectinload(TaskCheckinPhoto.file_asset).selectinload(FileAsset.variants))
        .where(
            TaskCheckinPhoto.id == photo_id,
            TaskCheckinPhoto.task_id == task_id,
            TaskCheckinPhoto.deleted_at.is_(None),
        )
    )
    if photo is None:
        raise APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="照片不存在", status_code=404)
    if not can_delete_checkin_photo(photo, user):
        raise APIError(code=ErrorCode.FORBIDDEN, message="权限不足", status_code=403)

    photo.deleted_at = now
    if photo.file_asset is not None and photo.file_asset.deleted_at is None:
        photo.file_asset.process_status = "deleted"
        photo.file_asset.deleted_at = now
        for variant in photo.file_asset.variants:
            if variant.deleted_at is None:
                variant.deleted_at = now
    db.commit()
    return {
        "photo_id": photo.id,
        "deleted_at": now,
    }
