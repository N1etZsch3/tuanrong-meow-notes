"""Admin write operations on tasks: publish, edit, status changes, soft delete.

Each public function owns exactly one transaction and commits at its end; helpers only
flush. Map-point synchronization and operation/activity logging happen inside the same
transaction as the state change they describe.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.errors import APIError
from app.modules.auth.models import AdminOperationLog, User
from app.modules.files.service import resolve_business_image
from app.modules.map.models import MapPoint
from app.modules.map.service import get_default_campus
from app.modules.tasks.constants import (
    EXECUTION_REMOVED_CANCEL_REASON,
    EXECUTION_STATUS_LABELS,
    TASK_ERROR_DUPLICATE_DATE,
    TASK_ERROR_EMPTY_DATES,
    TASK_ERROR_EXECUTION_NOT_FOUND,
    TASK_ERROR_INVALID_DATES,
    TASK_ERROR_MAP_POINT_INVALID,
    TASK_ERROR_PHOTO_INVALID,
    TASK_ERROR_STATUS_CONFLICT,
    TASK_STATUS_LABELS,
)
from app.modules.tasks.execution_state import (
    AUTO_ARCHIVE_CANCEL_REASON,
    PARENT_CANCEL_REASON,
    PARENT_COMPLETE_CANCEL_REASON,
    cancel_unfinished_execution_dates,
    normalize_task_lifecycle,
)
from app.modules.tasks.models import Task, TaskActivityLog, TaskExecutionDate, TaskPhoto
from app.modules.tasks.presenters import activity_payload, execution_payload
from app.modules.tasks.query_service import get_task_or_raise
from app.modules.tasks.schemas import (
    SummerFeedingTaskCreateRequest,
    SummerFeedingTaskUpdateRequest,
    TaskExecutionStatusUpdateRequest,
    TaskPhotoRequest,
    TaskStatusUpdateRequest,
    UploadedFileRef,
)


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _end_of_day(value: date) -> datetime:
    return datetime.combine(value, time.max, tzinfo=UTC)


def _task_no(now: datetime) -> str:
    return f"TF{now:%Y%m%d%H%M%S}{uuid4().hex[:6].upper()}"


def _normalize_dates(values: list[date] | None) -> list[date]:
    if not values:
        raise APIError(code=TASK_ERROR_EMPTY_DATES, message="执行日期不能为空", status_code=400)
    if len(set(values)) != len(values):
        raise APIError(code=TASK_ERROR_DUPLICATE_DATE, message="执行日期重复", status_code=409)
    try:
        return sorted(values)
    except TypeError as exc:
        raise APIError(
            code=TASK_ERROR_INVALID_DATES,
            message="执行日期不合法",
            status_code=400,
        ) from exc


def _clean_required_items(value: str | None) -> str:
    normalized = value.strip() if value else ""
    return normalized or "猫粮、水"


def _clean_description(value: str | None) -> str:
    normalized = value.strip() if value else ""
    return normalized or "暑假投喂"


def resolve_uploaded_file_urls(
    db: Session,
    photo: UploadedFileRef,
    *,
    uploaded_by: User,
    allowed_usage_types: set[str],
) -> tuple[UUID | None, str | None, str | None]:
    return resolve_business_image(
        db=db,
        current_user=uploaded_by,
        file_id=photo.file_id,
        file_url=photo.file_url,
        thumbnail_url=photo.thumbnail_url,
        allowed_usage_types=allowed_usage_types,
    )


def _sync_task_map_point_status(
    db: Session,
    *,
    task: Task,
    admin: User,
    now: datetime,
    soft_deleted: bool = False,
) -> None:
    point = db.get(MapPoint, task.map_point_id)
    if point is None:
        return

    point.updated_by = admin.id
    point.updated_at = now
    if soft_deleted:
        point.visibility = "hidden"
        point.status = "deleted"
        point.deleted_at = now
        return

    if point.deleted_at is not None:
        return

    if task.status in {"cancelled", "archived"}:
        point.visibility = "hidden"
        point.status = "active"
        return

    point.visibility = "public" if task.is_public else "admin_only"
    point.status = "active"


def _create_map_point(
    db: Session,
    *,
    payload: SummerFeedingTaskCreateRequest,
    admin: User,
) -> MapPoint:
    if payload.map_point_id:
        point = db.get(MapPoint, payload.map_point_id)
        if point is None or point.deleted_at is not None:
            raise APIError(
                code=TASK_ERROR_MAP_POINT_INVALID,
                message="地图点参数不合法",
                status_code=400,
            )
        return point
    if payload.map_point is None:
        raise APIError(
            code=TASK_ERROR_MAP_POINT_INVALID,
            message="地图点参数不合法",
            status_code=400,
        )

    campus = get_default_campus(db, payload.map_point.campus_id)
    point = MapPoint(
        campus_id=campus.id,
        area_id=payload.map_point.area_id,
        point_type="task",
        point_scope="long_term",
        name=payload.title,
        subtitle="暑假喂食任务",
        description=_clean_description(payload.description),
        location_name=payload.map_point.location_name,
        location_detail=payload.map_point.location_detail,
        lng=Decimal(str(payload.map_point.lng)),
        lat=Decimal(str(payload.map_point.lat)),
        geom=f"POINT({payload.map_point.lng} {payload.map_point.lat})",
        amap_poi_id=payload.map_point.amap_poi_id,
        amap_address=payload.map_point.amap_address,
        tencent_poi_id=payload.map_point.tencent_poi_id,
        tencent_poi_name=payload.map_point.tencent_poi_name,
        tencent_poi_address=payload.map_point.tencent_poi_address,
        tencent_poi_category=payload.map_point.tencent_poi_category,
        tencent_poi_lng=Decimal(str(payload.map_point.tencent_poi_lng))
        if payload.map_point.tencent_poi_lng is not None
        else None,
        tencent_poi_lat=Decimal(str(payload.map_point.tencent_poi_lat))
        if payload.map_point.tencent_poi_lat is not None
        else None,
        tencent_poi_distance_meters=payload.map_point.tencent_poi_distance_meters,
        tencent_poi_match_method=payload.map_point.tencent_poi_match_method,
        route_instruction=payload.map_point.route_instruction,
        landmark_hint=payload.map_point.landmark_hint,
        entrance_hint=payload.map_point.entrance_hint,
        icon_key="task_feeding",
        display_level=85,
        label_min_zoom=16,
        preview_enabled=True,
        preview_min_zoom=16,
        visibility="public" if payload.is_public else "admin_only",
        status="active",
        created_by=admin.id,
        updated_by=admin.id,
    )
    db.add(point)
    db.flush()
    return point


def _add_task_photos(
    db: Session,
    *,
    task: Task,
    photos: list[TaskPhotoRequest],
    uploaded_by: User,
) -> list[TaskPhoto]:
    created: list[TaskPhoto] = []
    cover_exists = any(photo.is_cover for photo in photos)
    for index, photo in enumerate(photos):
        file_id, file_url, thumbnail_url = resolve_uploaded_file_urls(
            db,
            photo,
            uploaded_by=uploaded_by,
            allowed_usage_types={"map_point_cover", "map_point_scene", "map_point_route"},
        )
        if not file_url:
            raise APIError(
                code=TASK_ERROR_PHOTO_INVALID,
                message="任务图片参数不合法",
                status_code=400,
            )
        is_cover = photo.is_cover or (index == 0 and not cover_exists)
        task_photo = TaskPhoto(
            task_id=task.id,
            file_id=file_id,
            file_url=file_url,
            thumbnail_url=thumbnail_url,
            cos_object_key=photo.cos_object_key,
            photo_type="cover" if is_cover else photo.photo_type,
            caption=photo.caption,
            sort_order=photo.sort_order if photo.sort_order is not None else index,
            is_cover=is_cover,
            uploaded_by=uploaded_by.id,
        )
        db.add(task_photo)
        created.append(task_photo)
    return created


def publish_summer_feeding_task(
    db: Session,
    *,
    admin: User,
    payload: SummerFeedingTaskCreateRequest,
    now: datetime,
) -> dict:
    execute_dates = _normalize_dates(payload.execute_dates)
    point = _create_map_point(db, payload=payload, admin=admin)
    task = Task(
        task_no=_task_no(now),
        title=payload.title,
        task_type="feeding",
        task_mode="recurring",
        schedule_type="selected_dates",
        completion_policy="per_execution_date",
        priority="normal",
        status="in_progress",
        map_point_id=point.id,
        area_id=point.area_id,
        publisher_id=admin.id,
        description=_clean_description(payload.description),
        route_instruction=point.route_instruction,
        required_items=_clean_required_items(payload.required_items),
        start_at=_start_of_day(execute_dates[0]),
        deadline_at=_end_of_day(execute_dates[-1]),
        published_at=now,
        is_public=payload.is_public,
    )
    db.add(task)
    db.flush()

    for execute_date in execute_dates:
        db.add(TaskExecutionDate(task_id=task.id, execute_date=execute_date, status="pending"))

    photos = _add_task_photos(db, task=task, photos=payload.photos, uploaded_by=admin)
    admin_name = admin.profile.nickname if admin.profile else admin.student_no
    db.add(
        TaskActivityLog(
            task_id=task.id,
            activity_type="created",
            title="系统生成本次投喂任务",
            content=f"{admin_name} 发布了暑假投喂任务",
            actor_id=admin.id,
            activity_metadata={"execute_dates": [item.isoformat() for item in execute_dates]},
            created_at=now,
        )
    )
    db.add(
        AdminOperationLog(
            admin_id=admin.id,
            operation_type="publish",
            target_type="task",
            target_id=task.id,
            summary=f"发布暑假喂食任务：{task.title}",
            before_data=None,
            after_data={"task_id": str(task.id), "map_point_id": str(point.id)},
        )
    )
    db.commit()
    return {
        "task_id": task.id,
        "task_no": task.task_no,
        "map_point_id": point.id,
        "task_type": task.task_type,
        "task_mode": task.task_mode,
        "schedule_type": task.schedule_type,
        "completion_policy": task.completion_policy,
        "status": task.status,
        "execution_date_count": len(execute_dates),
        "photo_count": len(photos),
        "published_at": task.published_at,
    }


def update_summer_feeding_task(
    db: Session,
    *,
    task_id: UUID,
    admin: User,
    payload: SummerFeedingTaskUpdateRequest,
    today: date,
    now: datetime,
) -> dict:
    task = get_task_or_raise(db, task_id, include_private=True)
    if task.status not in {"in_progress", "completed", "cancelled", "archived"}:
        raise APIError(
            code=TASK_ERROR_STATUS_CONFLICT,
            message="当前任务状态不允许修改",
            status_code=409,
        )
    if payload.title is not None:
        task.title = payload.title
        task.map_point.name = payload.title
    if payload.description is not None:
        task.description = _clean_description(payload.description)
        task.map_point.description = task.description
    if payload.required_items is not None:
        task.required_items = _clean_required_items(payload.required_items)
    if payload.map_point is not None:
        task.map_point.lng = Decimal(str(payload.map_point.lng))
        task.map_point.lat = Decimal(str(payload.map_point.lat))
        task.map_point.geom = f"POINT({payload.map_point.lng} {payload.map_point.lat})"
        task.map_point.location_name = payload.map_point.location_name
        task.map_point.location_detail = payload.map_point.location_detail
        task.map_point.route_instruction = payload.map_point.route_instruction
        task.map_point.landmark_hint = payload.map_point.landmark_hint
        task.map_point.entrance_hint = payload.map_point.entrance_hint
        task.map_point.amap_poi_id = payload.map_point.amap_poi_id
        task.map_point.amap_address = payload.map_point.amap_address
        task.map_point.tencent_poi_id = payload.map_point.tencent_poi_id
        task.map_point.tencent_poi_name = payload.map_point.tencent_poi_name
        task.map_point.tencent_poi_address = payload.map_point.tencent_poi_address
        task.map_point.tencent_poi_category = payload.map_point.tencent_poi_category
        task.map_point.tencent_poi_lng = (
            Decimal(str(payload.map_point.tencent_poi_lng))
            if payload.map_point.tencent_poi_lng is not None
            else None
        )
        task.map_point.tencent_poi_lat = (
            Decimal(str(payload.map_point.tencent_poi_lat))
            if payload.map_point.tencent_poi_lat is not None
            else None
        )
        task.map_point.tencent_poi_distance_meters = payload.map_point.tencent_poi_distance_meters
        task.map_point.tencent_poi_match_method = payload.map_point.tencent_poi_match_method
        task.route_instruction = payload.map_point.route_instruction
    if payload.execute_dates is not None:
        execute_dates = _normalize_dates(payload.execute_dates)
        existing = {
            item.execute_date: item
            for item in task.execution_dates
            if item.deleted_at is None
        }
        for execute_date in execute_dates:
            if execute_date not in existing:
                task.execution_dates.append(
                    TaskExecutionDate(
                        execute_date=execute_date,
                        status="pending",
                    )
                )
        for execute_date, execution in existing.items():
            if execute_date not in execute_dates and execution.status != "completed":
                execution.status = "cancelled"
                execution.cancelled_at = now
                execution.cancelled_by = admin.id
                execution.cancel_reason = EXECUTION_REMOVED_CANCEL_REASON
                execution.remark = execution.remark or EXECUTION_REMOVED_CANCEL_REASON
        task.start_at = _start_of_day(execute_dates[0])
        task.deadline_at = _end_of_day(execute_dates[-1])
    if payload.photos is not None:
        for photo in task.photos:
            photo.deleted_at = now
        _add_task_photos(db, task=task, photos=payload.photos, uploaded_by=admin)

    admin_name = admin.profile.nickname if admin.profile else admin.student_no
    db.add(
        TaskActivityLog(
            task_id=task.id,
            activity_type="updated",
            title="任务已更新",
            content=f"{admin_name} 修改了任务信息",
            actor_id=admin.id,
            created_at=now,
        )
    )
    task.updated_at = now
    normalize_task_lifecycle(task, today=today, now=now)
    db.commit()
    return {"task_id": task.id, "updated_at": task.updated_at}


def update_task_status(
    db: Session,
    *,
    task_id: UUID,
    admin: User,
    payload: TaskStatusUpdateRequest,
    now: datetime,
) -> dict:
    task = get_task_or_raise(db, task_id, include_private=True)
    task.status = payload.status
    if payload.status == "cancelled":
        task.cancelled_at = now
    else:
        task.cancelled_at = None
    if payload.status == "completed":
        task.completed_at = now
    elif payload.status in {"in_progress", "cancelled"}:
        task.completed_at = None
    if payload.status == "archived":
        task.completed_at = task.completed_at or now
    if payload.status in {"completed", "cancelled", "archived"}:
        cancel_reasons = {
            "completed": PARENT_COMPLETE_CANCEL_REASON,
            "cancelled": PARENT_CANCEL_REASON,
            "archived": AUTO_ARCHIVE_CANCEL_REASON,
        }
        cancel_unfinished_execution_dates(
            task.execution_dates,
            now=now,
            reason=cancel_reasons[payload.status],
            cancelled_by=admin.id,
        )
    task.updated_at = now
    _sync_task_map_point_status(db, task=task, admin=admin, now=now)
    db.add(
        TaskActivityLog(
            task_id=task.id,
            activity_type=payload.status,
            title=TASK_STATUS_LABELS.get(payload.status, payload.status),
            content=payload.reason,
            actor_id=admin.id,
            activity_metadata={"reason": payload.reason} if payload.reason else None,
            created_at=now,
        )
    )
    db.commit()
    return {"task_id": task.id, "status": task.status, "updated_at": task.updated_at}


def update_task_execution_status(
    db: Session,
    *,
    task_id: UUID,
    execution_date_id: UUID,
    admin: User,
    payload: TaskExecutionStatusUpdateRequest,
    today: date,
    now: datetime,
) -> dict:
    """Adjust one execution date while keeping parent lifecycle and map state consistent."""
    task = get_task_or_raise(db, task_id, include_private=True)
    execution = next(
        (
            item
            for item in task.execution_dates
            if item.id == execution_date_id and item.deleted_at is None
        ),
        None,
    )
    if execution is None:
        raise APIError(
            code=TASK_ERROR_EXECUTION_NOT_FOUND,
            message="执行日期不存在",
            status_code=404,
        )
    if task.status in {"cancelled", "archived"} and payload.status in {
        "pending",
        "completed",
    }:
        raise APIError(
            code=TASK_ERROR_STATUS_CONFLICT,
            message="请先恢复父任务，再调整子任务状态",
            status_code=409,
        )

    previous_status = execution.status
    execution.status = payload.status
    execution.updated_at = now
    if payload.remark is not None:
        execution.remark = payload.remark or None

    if payload.status == "completed":
        execution.completed_by = admin.id
        execution.completed_at = now
        execution.cancelled_by = None
        execution.cancelled_at = None
        execution.cancel_reason = None
    elif payload.status == "pending":
        execution.completed_by = None
        execution.completed_at = None
        execution.checkin_id = None
        execution.cancelled_by = None
        execution.cancelled_at = None
        execution.cancel_reason = None
    else:
        execution.completed_by = None
        execution.completed_at = None
        execution.checkin_id = None
        execution.cancelled_by = admin.id
        execution.cancelled_at = now
        execution.cancel_reason = payload.reason

    status_label = EXECUTION_STATUS_LABELS[payload.status]
    activity = TaskActivityLog(
        task_id=task.id,
        task_execution_date_id=execution.id,
        activity_type=f"execution_{payload.status}",
        title=f"子任务{status_label}",
        content=(
            payload.reason
            or f"管理员将 {execution.execute_date.isoformat()} 的子任务调整为{status_label}"
        ),
        actor_id=admin.id,
        activity_metadata={
            "execute_date": execution.execute_date.isoformat(),
            "previous_status": previous_status,
            "status": payload.status,
            "reason": payload.reason,
        },
        created_at=now,
    )
    db.add(activity)

    task.updated_at = now
    normalize_task_lifecycle(task, today=today, now=now)
    _sync_task_map_point_status(db, task=task, admin=admin, now=now)
    db.add(
        AdminOperationLog(
            admin_id=admin.id,
            operation_type="update_status",
            target_type="task_execution_date",
            target_id=execution.id,
            summary=(
                f"调整子任务 {execution.execute_date.isoformat()} 状态："
                f"{EXECUTION_STATUS_LABELS.get(previous_status, previous_status)} -> {status_label}"
            ),
            before_data={"status": previous_status},
            after_data={
                "status": payload.status,
                "reason": payload.reason,
                "remark": execution.remark,
            },
        )
    )
    db.commit()
    return {
        "task_id": task.id,
        "task_status": task.status,
        "execution_date": execution_payload(execution, today=today),
        "activity": activity_payload(activity),
    }


def soft_delete_task(
    db: Session,
    *,
    task_id: UUID,
    admin: User,
    now: datetime,
) -> dict:
    task = get_task_or_raise(db, task_id, include_private=True)
    task.deleted_at = now
    task.updated_at = now
    _sync_task_map_point_status(db, task=task, admin=admin, now=now, soft_deleted=True)
    admin_name = admin.profile.nickname if admin.profile else admin.student_no
    db.add(
        TaskActivityLog(
            task_id=task.id,
            activity_type="deleted",
            title="任务已删除",
            content=f"{admin_name} 删除了任务",
            actor_id=admin.id,
            created_at=now,
        )
    )
    db.add(
        AdminOperationLog(
            admin_id=admin.id,
            operation_type="delete",
            target_type="task",
            target_id=task.id,
            summary=f"删除暑假喂食任务：{task.title}",
            before_data={"task_id": str(task.id), "map_point_id": str(task.map_point_id)},
            after_data={"deleted_at": now.isoformat()},
        )
    )
    db.commit()
    return {"task_id": task.id, "deleted_at": task.deleted_at}
