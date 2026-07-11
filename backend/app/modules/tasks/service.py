from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import APIError, ErrorCode
from app.modules.auth.models import AdminOperationLog, User
from app.modules.files.models import FileAsset
from app.modules.files.service import resolve_business_image
from app.modules.map.models import MapPoint
from app.modules.map.service import associated_poi_payload, get_default_campus
from app.modules.tasks.execution_state import (
    AUTO_ARCHIVE_CANCEL_REASON,
    PARENT_CANCEL_REASON,
    PARENT_COMPLETE_CANCEL_REASON,
    active_execution,
    active_execution_dates,
    cancel_unfinished_execution_dates,
    execution_display_status,
    execution_display_status_label,
    normalize_task_lifecycle,
)
from app.modules.tasks.models import (
    Task,
    TaskActivityLog,
    TaskCheckin,
    TaskCheckinPhoto,
    TaskExecutionDate,
    TaskPhoto,
)
from app.modules.tasks.schemas import (
    SummerFeedingTaskCreateRequest,
    SummerFeedingTaskUpdateRequest,
    TaskCheckinRequest,
    TaskPhotoRequest,
    TaskStatusUpdateRequest,
    UploadedFileRef,
)

TASK_STATUS_LABELS = {
    "pending": "待发布",
    "in_progress": "进行中",
    "completed": "已完成",
    "cancelled": "已取消",
    "archived": "已归档",
}

TASK_ERROR_PARAM = 62001
TASK_ERROR_EMPTY_DATES = 62002
TASK_ERROR_INVALID_DATES = 62003
TASK_ERROR_UNSUPPORTED_TYPE = 62004
TASK_ERROR_DUPLICATE_DATE = 62006
TASK_ERROR_NOT_EXECUTION_DAY = 62007
TASK_ERROR_EXECUTION_COMPLETED = 62008
TASK_ERROR_EXECUTION_NOT_FOUND = 62009
TASK_ERROR_NOT_FOUND = 62010
TASK_ERROR_PHOTO_INVALID = 62011
TASK_ERROR_MAP_POINT_INVALID = 62012
TASK_ERROR_STATUS_CONFLICT = 62013
TASK_ERROR_CANCELLED_CANNOT_CHECKIN = 62015

LOCAL_TZ = ZoneInfo("Asia/Shanghai")
EXECUTION_REMOVED_CANCEL_REASON = "管理员调整执行日期，该子任务自动取消"


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _today() -> date:
    return _now().astimezone(LOCAL_TZ).date()


def _local_date_text(value: datetime) -> str:
    return value.astimezone(LOCAL_TZ).date().isoformat()


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


def _user_payload(user: User | None) -> dict | None:
    if user is None:
        return None
    return {
        "user_id": user.id,
        "nickname": user.profile.nickname if user.profile else user.student_no,
        "avatar_url": user.profile.avatar_url if user.profile else None,
    }


def _task_base_statement():
    return select(Task).options(
        selectinload(Task.map_point),
        selectinload(Task.publisher).selectinload(User.profile),
        selectinload(Task.photos).selectinload(TaskPhoto.file_asset),
        selectinload(Task.execution_dates).selectinload(TaskExecutionDate.completed_user),
        selectinload(Task.activities).selectinload(TaskActivityLog.actor).selectinload(User.profile),
        selectinload(Task.checkins).selectinload(TaskCheckin.submitter).selectinload(User.profile),
        selectinload(Task.checkins)
        .selectinload(TaskCheckin.photos)
        .selectinload(TaskCheckinPhoto.file_asset),
        selectinload(Task.checkins)
        .selectinload(TaskCheckin.photos)
        .selectinload(TaskCheckinPhoto.uploader)
        .selectinload(User.profile),
    )


def get_task_or_raise(db: Session, task_id: UUID, *, include_private: bool = False) -> Task:
    statement = _task_base_statement().where(Task.id == task_id, Task.deleted_at.is_(None))
    if not include_private:
        statement = statement.where(Task.is_public.is_(True))
    task = db.scalar(statement)
    if task is None:
        raise APIError(code=TASK_ERROR_NOT_FOUND, message="任务不存在", status_code=404)
    return task


def get_task_by_map_point(db: Session, map_point_id: UUID) -> Task | None:
    return db.scalar(
        _task_base_statement().where(
            Task.map_point_id == map_point_id,
            Task.deleted_at.is_(None),
        )
    )


def _date_range_payload(execution_dates: list[TaskExecutionDate]) -> dict:
    active_dates = active_execution_dates(execution_dates)
    if not active_dates:
        return {
            "start_date": None,
            "end_date": None,
            "total_count": 0,
            "completed_count": 0,
            "pending_count": 0,
            "cancelled_count": 0,
            "skipped_count": 0,
            "missed_count": 0,
        }
    counts = {status: sum(1 for item in active_dates if item.status == status) for status in {
        "completed",
        "pending",
        "cancelled",
        "skipped",
        "missed",
    }}
    sorted_dates = sorted(active_dates, key=lambda item: item.execute_date)
    return {
        "start_date": sorted_dates[0].execute_date.isoformat(),
        "end_date": sorted_dates[-1].execute_date.isoformat(),
        "total_count": len(active_dates),
        "completed_count": counts["completed"],
        "pending_count": counts["pending"],
        "cancelled_count": counts["cancelled"],
        "skipped_count": counts["skipped"],
        "missed_count": counts["missed"],
    }


def _execution_payload(
    execution_date: TaskExecutionDate | None,
    *,
    today: date | None = None,
) -> dict | None:
    if execution_date is None:
        return None
    display_status = execution_display_status(execution_date, today=today or _today())
    return {
        "execution_date_id": execution_date.id,
        "execute_date": execution_date.execute_date.isoformat(),
        "status": execution_date.status,
        "display_status": display_status,
        "display_status_label": execution_display_status_label(display_status),
        "completed_by": _user_payload(execution_date.completed_user),
        "completed_at": execution_date.completed_at,
        "checkin_id": execution_date.checkin_id,
        "remark": execution_date.remark,
    }


def _next_execution(
    execution_dates: list[TaskExecutionDate],
    today: date | None = None,
) -> TaskExecutionDate | None:
    today = today or _today()
    active_dates = active_execution_dates(execution_dates)
    future_pending = [
        item
        for item in active_dates
        if item.status == "pending" and item.execute_date >= today
    ]
    if future_pending:
        return future_pending[0]
    pending = [item for item in active_dates if item.status == "pending"]
    return pending[0] if pending else None


def _current_execution(
    execution_dates: list[TaskExecutionDate],
    current_date: date | None = None,
) -> TaskExecutionDate | None:
    current_date = current_date or _today()
    return active_execution(execution_dates, today=current_date)


def _split_statuses(value: str | None) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()] if value else []


def _date_in_query_window(
    value: date,
    *,
    execute_date: date | None = None,
    execute_date_start: date | None = None,
    execute_date_end: date | None = None,
) -> bool:
    if execute_date is not None:
        return value == execute_date
    if execute_date_start is not None and value < execute_date_start:
        return False
    if execute_date_end is not None and value > execute_date_end:
        return False
    return True


def _normalize_task_lifecycle(task: Task, *, today: date | None = None) -> bool:
    return normalize_task_lifecycle(task, today=today or _today(), now=_now())


def _execution_matches_filters(
    execution_date: TaskExecutionDate,
    *,
    execute_date: date | None = None,
    execute_date_start: date | None = None,
    execute_date_end: date | None = None,
    execution_statuses: set[str] | None = None,
    execution_display_statuses: set[str] | None = None,
    today: date,
) -> bool:
    if not _date_in_query_window(
        execution_date.execute_date,
        execute_date=execute_date,
        execute_date_start=execute_date_start,
        execute_date_end=execute_date_end,
    ):
        return False
    if execution_statuses and execution_date.status not in execution_statuses:
        return False
    display_status = execution_display_status(execution_date, today=today)
    if execution_display_statuses and display_status not in execution_display_statuses:
        return False
    return True


def _display_executions_payload(
    execution_dates: list[TaskExecutionDate],
    *,
    execute_date: date | None = None,
    execute_date_start: date | None = None,
    execute_date_end: date | None = None,
    execution_status: str | None = None,
    execution_display_status: str | None = None,
    today: date,
) -> list[dict]:
    storage_statuses = set(_split_statuses(execution_status))
    display_statuses = set(_split_statuses(execution_display_status))
    has_filter = bool(
        execute_date
        or execute_date_start
        or execute_date_end
        or storage_statuses
        or display_statuses
    )
    active_dates = active_execution_dates(execution_dates)
    if has_filter:
        active_dates = [
            item
            for item in active_dates
            if _execution_matches_filters(
                item,
                execute_date=execute_date,
                execute_date_start=execute_date_start,
                execute_date_end=execute_date_end,
                execution_statuses=storage_statuses,
                execution_display_statuses=display_statuses,
                today=today,
            )
        ]
    return [_execution_payload(item, today=today) for item in active_dates]


def _list_display_execution(
    execution_dates: list[TaskExecutionDate],
    *,
    execute_date: date | None = None,
    execute_date_start: date | None = None,
    execute_date_end: date | None = None,
    execution_status: str | None = None,
    execution_display_status: str | None = None,
    today: date | None = None,
) -> TaskExecutionDate | None:
    today = today or _today()
    active_dates = active_execution_dates(execution_dates)
    statuses = set(_split_statuses(execution_status))
    display_statuses = set(_split_statuses(execution_display_status))
    has_execution_filter = bool(
        execute_date or execute_date_start or execute_date_end or statuses or display_statuses
    )
    if not has_execution_filter:
        return _current_execution(active_dates, current_date=today)

    matching = [
        item
        for item in active_dates
        if _execution_matches_filters(
            item,
            execute_date=execute_date,
            execute_date_start=execute_date_start,
            execute_date_end=execute_date_end,
            execution_statuses=statuses,
            execution_display_statuses=display_statuses,
            today=today,
        )
    ]
    if not matching:
        return _current_execution(active_dates, current_date=today)

    upcoming = [item for item in matching if item.execute_date >= today]
    return upcoming[0] if upcoming else matching[-1]


def _asset_backed_photo_urls(photo: TaskPhoto | TaskCheckinPhoto) -> tuple[str, str | None]:
    asset = getattr(photo, "file_asset", None)
    if asset is not None and asset.deleted_at is None:
        return (
            asset.default_url or photo.file_url,
            asset.default_thumb_url or photo.thumbnail_url,
        )
    return photo.file_url, photo.thumbnail_url


def _resolve_uploaded_file_urls(
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


def _photo_payload(photo: TaskPhoto) -> dict:
    file_url, thumbnail_url = _asset_backed_photo_urls(photo)
    return {
        "photo_id": photo.id,
        "file_id": photo.file_id,
        "file_url": file_url,
        "thumbnail_url": thumbnail_url,
        "cos_object_key": photo.cos_object_key,
        "photo_type": photo.photo_type,
        "caption": photo.caption,
        "sort_order": photo.sort_order,
        "is_cover": photo.is_cover,
        "created_at": photo.created_at,
    }


def _is_admin(user: User | None) -> bool:
    return user is not None and user.role in {"admin", "super_admin"}


def _can_delete_checkin_photo(photo: TaskCheckinPhoto, viewer: User | None) -> bool:
    return bool(_is_admin(viewer) or (viewer is not None and photo.uploaded_by == viewer.id))


def _checkin_photo_payload(photo: TaskCheckinPhoto, viewer: User | None) -> dict:
    file_url, thumbnail_url = _asset_backed_photo_urls(photo)
    return {
        "photo_id": photo.id,
        "checkin_id": photo.checkin_id,
        "task_id": photo.task_id,
        "file_id": photo.file_id,
        "file_url": file_url,
        "thumbnail_url": thumbnail_url,
        "caption": photo.caption,
        "sort_order": photo.sort_order,
        "uploaded_by": _user_payload(photo.uploader),
        "can_delete": _can_delete_checkin_photo(photo, viewer),
        "created_at": photo.created_at,
    }


def _task_checkin_photos_payload(
    task: Task,
    viewer: User | None,
    *,
    execution_date_id: UUID | None = None,
) -> list[dict]:
    photos: list[tuple[datetime, int, TaskCheckinPhoto]] = []
    for checkin in task.checkins:
        if checkin.deleted_at is not None:
            continue
        if execution_date_id is not None and checkin.task_execution_date_id != execution_date_id:
            continue
        submitted_at = checkin.submitted_at or checkin.created_at
        for photo in checkin.photos:
            if photo.deleted_at is None:
                photos.append((submitted_at, photo.sort_order, photo))

    ordered_photos = sorted(photos, key=lambda item: item[1])
    ordered_photos = sorted(ordered_photos, key=lambda item: item[0], reverse=True)
    return [
        _checkin_photo_payload(photo, viewer)
        for _, _, photo in ordered_photos
    ]


def _checkin_record_payload(checkin: TaskCheckin, viewer: User | None) -> dict:
    return {
        "checkin_id": checkin.id,
        "task_execution_date_id": checkin.task_execution_date_id,
        "execute_date": checkin.execute_date,
        "submitter": _user_payload(checkin.submitter),
        "is_completed": checkin.is_completed,
        "process_result": checkin.process_result,
        "remark": checkin.remark,
        "submitted_at": checkin.submitted_at,
        "photos": [
            _checkin_photo_payload(photo, viewer)
            for photo in sorted(checkin.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None
        ],
    }


def _task_checkins_payload(
    task: Task,
    viewer: User | None,
    *,
    execution_date_id: UUID | None = None,
) -> list[dict]:
    checkins = [
        checkin
        for checkin in task.checkins
        if checkin.deleted_at is None
        and (execution_date_id is None or checkin.task_execution_date_id == execution_date_id)
    ]
    checkins.sort(key=lambda item: item.submitted_at or item.created_at, reverse=True)
    return [_checkin_record_payload(checkin, viewer) for checkin in checkins]


def _activities_payload(
    activities: list[TaskActivityLog],
    *,
    execution_date_id: UUID | None = None,
    limit: int | None = None,
) -> list[dict]:
    filtered = [
        activity
        for activity in sorted(activities, key=lambda item: item.created_at, reverse=True)
        if execution_date_id is None or activity.task_execution_date_id == execution_date_id
    ]
    if limit is not None:
        filtered = filtered[:limit]
    return [_activity_payload(activity) for activity in filtered]


def _execution_groups_payload(
    task: Task,
    *,
    viewer: User | None,
    today: date,
) -> list[dict]:
    return [
        {
            "execution": _execution_payload(execution, today=today),
            "activities": _activities_payload(
                task.activities,
                execution_date_id=execution.id,
            ),
            "checkin_photos": _task_checkin_photos_payload(
                task,
                viewer,
                execution_date_id=execution.id,
            ),
        }
        for execution in active_execution_dates(task.execution_dates)
    ]


def _cover_photo_url(task: Task) -> str | None:
    photos = [photo for photo in task.photos if photo.deleted_at is None]
    cover = next((photo for photo in photos if photo.is_cover), None)
    if cover:
        file_url, thumbnail_url = _asset_backed_photo_urls(cover)
        return thumbnail_url or file_url
    first_photo = min(photos, key=lambda item: item.sort_order, default=None)
    if first_photo is None:
        return None
    file_url, thumbnail_url = _asset_backed_photo_urls(first_photo)
    return thumbnail_url or file_url


def _map_point_payload(point: MapPoint) -> dict:
    return {
        "map_point_id": point.id,
        "campus_id": point.campus_id,
        "area_id": point.area_id,
        "point_type": point.point_type,
        "point_scope": point.point_scope,
        "name": point.name,
        "lng": float(point.lng),
        "lat": float(point.lat),
        "location_name": point.location_name,
        "location_detail": point.location_detail,
        "route_instruction": point.route_instruction,
        "landmark_hint": point.landmark_hint,
        "entrance_hint": point.entrance_hint,
        "amap_poi_id": point.amap_poi_id,
        "amap_address": point.amap_address,
        "tencent_poi_id": point.tencent_poi_id,
        "tencent_poi_name": point.tencent_poi_name,
        "tencent_poi_address": point.tencent_poi_address,
        "tencent_poi_category": point.tencent_poi_category,
        "tencent_poi_lng": (
            float(point.tencent_poi_lng) if point.tencent_poi_lng is not None else None
        ),
        "tencent_poi_lat": (
            float(point.tencent_poi_lat) if point.tencent_poi_lat is not None else None
        ),
        "tencent_poi_distance_meters": point.tencent_poi_distance_meters,
        "tencent_poi_match_method": point.tencent_poi_match_method,
        "associated_poi": associated_poi_payload(point),
    }


def _activity_payload(activity: TaskActivityLog) -> dict:
    execute_date = None
    if activity.activity_metadata:
        execute_date = activity.activity_metadata.get("execute_date")
    return {
        "activity_id": activity.id,
        "activity_type": activity.activity_type,
        "title": activity.title,
        "content": activity.content,
        "actor": _user_payload(activity.actor),
        "task_execution_date_id": activity.task_execution_date_id,
        "execute_date": execute_date,
        "created_at": activity.created_at,
        "metadata": activity.activity_metadata or {},
    }


def task_list_item_payload(
    task: Task,
    *,
    execute_date: date | None = None,
    execute_date_start: date | None = None,
    execute_date_end: date | None = None,
    execution_status: str | None = None,
    execution_display_status: str | None = None,
    today: date | None = None,
) -> dict:
    today = today or _today()
    current_execution = _list_display_execution(
        task.execution_dates,
        execute_date=execute_date,
        execute_date_start=execute_date_start,
        execute_date_end=execute_date_end,
        execution_status=execution_status,
        execution_display_status=execution_display_status,
        today=today,
    )
    next_execution = _next_execution(task.execution_dates, today=today)
    display_executions = _display_executions_payload(
        task.execution_dates,
        execute_date=execute_date,
        execute_date_start=execute_date_start,
        execute_date_end=execute_date_end,
        execution_status=execution_status,
        execution_display_status=execution_display_status,
        today=today,
    )
    return {
        "task_id": task.id,
        "title": task.title,
        "task_type": task.task_type,
        "status": task.status,
        "status_label": TASK_STATUS_LABELS.get(task.status, task.status),
        "description": task.description,
        "required_items": task.required_items,
        "cover_photo_url": _cover_photo_url(task),
        "map_point": {
            "map_point_id": task.map_point.id,
            "location_name": task.map_point.location_name,
            "location_detail": task.map_point.location_detail,
            "lng": float(task.map_point.lng),
            "lat": float(task.map_point.lat),
        },
        "date_range": _date_range_payload(task.execution_dates),
        "current_execution": _execution_payload(current_execution, today=today),
        "next_execution": _execution_payload(next_execution, today=today),
        "display_executions": display_executions,
        "distance_meters": None,
        "published_at": task.published_at,
    }


def _checkin_disabled_reason(
    task: Task,
    current_execution: TaskExecutionDate | None,
    *,
    today: date,
) -> str | None:
    if task.status != "in_progress":
        return "任务当前状态不可完成"
    if current_execution is None:
        return "暂无执行日期"
    if current_execution.status == "completed":
        return "该日期已完成"
    if current_execution.status not in {"pending", "missed"}:
        return "该日期不可完成"
    if current_execution.execute_date > today:
        return "未到任务日期"
    return None


def task_detail_payload(
    task: Task,
    *,
    current_date: date | None = None,
    execution_date_id: UUID | None = None,
    activity_limit: int = 20,
    can_admin_edit: bool = False,
    viewer: User | None = None,
) -> dict:
    today = current_date or _today()
    selected_execution = None
    if execution_date_id is not None:
        selected_execution = next(
            (
                item
                for item in task.execution_dates
                if item.id == execution_date_id and item.deleted_at is None
            ),
            None,
        )
        if selected_execution is None:
            raise APIError(
                code=TASK_ERROR_EXECUTION_NOT_FOUND,
                message="执行日期不存在",
                status_code=404,
            )
    current_execution = selected_execution or _current_execution(
        task.execution_dates,
        current_date=today,
    )
    next_execution = _next_execution(task.execution_dates, today=today)
    checkin_disabled_reason = _checkin_disabled_reason(
        task,
        current_execution,
        today=today,
    )
    scoped_execution_id = selected_execution.id if selected_execution is not None else None
    return {
        "task_id": task.id,
        "task_no": task.task_no,
        "title": task.title,
        "task_type": task.task_type,
        "task_mode": task.task_mode,
        "schedule_type": task.schedule_type,
        "completion_policy": task.completion_policy,
        "status": task.status,
        "status_label": TASK_STATUS_LABELS.get(task.status, task.status),
        "description": task.description,
        "required_items": task.required_items,
        "date_range": _date_range_payload(task.execution_dates),
        "current_execution": _execution_payload(current_execution, today=today),
        "next_execution": _execution_payload(next_execution, today=today),
        "display_executions": _display_executions_payload(task.execution_dates, today=today),
        "detail_scope": "execution" if selected_execution is not None else "parent",
        "active_execution_id": current_execution.id if current_execution is not None else None,
        "execution": (
            _execution_payload(selected_execution, today=today)
            if selected_execution is not None
            else None
        ),
        "map_point": _map_point_payload(task.map_point),
        "photos": [
            _photo_payload(photo)
            for photo in sorted(task.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None
        ],
        "checkin_photos": _task_checkin_photos_payload(
            task,
            viewer,
            execution_date_id=scoped_execution_id,
        ),
        "checkins": _task_checkins_payload(
            task,
            viewer,
            execution_date_id=scoped_execution_id,
        ),
        "execution_dates": [
            _execution_payload(item, today=today)
            for item in sorted(task.execution_dates, key=lambda item: item.execute_date)
            if item.deleted_at is None
        ],
        "execution_groups": _execution_groups_payload(task, viewer=viewer, today=today),
        "activities": _activities_payload(
            task.activities,
            execution_date_id=scoped_execution_id,
            limit=activity_limit,
        ),
        "actions": {
            "can_navigate": True,
            "can_checkin": checkin_disabled_reason is None,
            "checkin_disabled_reason": checkin_disabled_reason,
            "can_admin_edit": can_admin_edit,
        },
        "published_at": task.published_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def _task_statement_for_list(*, include_private: bool = False):
    statement = _task_base_statement().where(
        Task.deleted_at.is_(None),
        Task.task_type == "feeding",
    )
    if not include_private:
        statement = statement.where(Task.is_public.is_(True))
    return statement


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
    if task_type and task_type != "feeding":
        raise APIError(
            code=TASK_ERROR_UNSUPPORTED_TYPE,
            message="只支持暑假喂食任务",
            status_code=400,
        )
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    today = _today()
    statement = _task_statement_for_list(include_private=include_private)
    if status:
        statuses = _split_statuses(status)
        if statuses:
            statement = statement.where(Task.status.in_(statuses))
    normalized_keyword = keyword.strip() if keyword else ""
    if normalized_keyword:
        statement = statement.join(MapPoint, MapPoint.id == Task.map_point_id).where(
            or_(
                Task.title.contains(normalized_keyword),
                MapPoint.location_name.contains(normalized_keyword),
                MapPoint.location_detail.contains(normalized_keyword),
            )
        )
    query_date = today if only_today else execute_date
    execution_statuses = _split_statuses(execution_status)
    if query_date or execute_date_start or execute_date_end or execution_statuses:
        task_ids = select(TaskExecutionDate.task_id).where(
            TaskExecutionDate.deleted_at.is_(None),
        )
        if query_date:
            task_ids = task_ids.where(TaskExecutionDate.execute_date == query_date)
        else:
            if execute_date_start:
                task_ids = task_ids.where(TaskExecutionDate.execute_date >= execute_date_start)
            if execute_date_end:
                task_ids = task_ids.where(TaskExecutionDate.execute_date <= execute_date_end)
        if execution_statuses:
            task_ids = task_ids.where(TaskExecutionDate.status.in_(execution_statuses))
        statement = statement.where(Task.id.in_(task_ids))

    tasks = db.scalars(statement.order_by(Task.start_at.asc(), Task.published_at.desc())).all()
    changed = False
    for task in tasks:
        changed = _normalize_task_lifecycle(task, today=today) or changed
    if changed:
        db.commit()
        tasks = db.scalars(statement.order_by(Task.start_at.asc(), Task.published_at.desc())).all()

    has_child_filter = bool(
        query_date
        or execute_date_start
        or execute_date_end
        or execution_status
        or execution_display_status
    )
    if has_child_filter:
        tasks = [
            task
            for task in tasks
            if _display_executions_payload(
                task.execution_dates,
                execute_date=query_date,
                execute_date_start=execute_date_start,
                execute_date_end=execute_date_end,
                execution_status=execution_status,
                execution_display_status=execution_display_status,
                today=today,
            )
        ]
    total = len(tasks)
    start = (page - 1) * page_size
    paged = tasks[start : start + page_size]
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
        file_id, file_url, thumbnail_url = _resolve_uploaded_file_urls(
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
) -> dict:
    execute_dates = _normalize_dates(payload.execute_dates)
    now = _now()
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
    task = get_task_or_raise(db, task_id, include_private=include_private)
    if _normalize_task_lifecycle(task, today=current_date or _today()):
        db.commit()
        task = get_task_or_raise(db, task_id, include_private=include_private)
    return task_detail_payload(
        task,
        current_date=current_date,
        execution_date_id=execution_date_id,
        activity_limit=activity_limit,
        can_admin_edit=can_admin_edit,
        viewer=viewer,
    )


def _checkin_photo(
    db: Session,
    *,
    task_id: UUID,
    checkin_id: UUID,
    photo: UploadedFileRef,
    uploaded_by: User,
    sort_order: int,
) -> TaskCheckinPhoto:
    file_id, file_url, thumbnail_url = _resolve_uploaded_file_urls(
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
) -> dict:
    task = get_task_or_raise(db, task_id)
    today = _today()
    if _normalize_task_lifecycle(task, today=today):
        db.commit()
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

    now = _now()
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
    _normalize_task_lifecycle(task, today=today)
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
            "submitter": _user_payload(user),
            "is_completed": checkin.is_completed,
            "process_result": checkin.process_result,
            "remark": checkin.remark,
            "submitted_at": checkin.submitted_at,
            "photos": [
                _checkin_photo_payload(photo, user)
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
    if not _can_delete_checkin_photo(photo, user):
        raise APIError(code=ErrorCode.FORBIDDEN, message="权限不足", status_code=403)

    deleted_at = _now()
    photo.deleted_at = deleted_at
    if photo.file_asset is not None and photo.file_asset.deleted_at is None:
        photo.file_asset.process_status = "deleted"
        photo.file_asset.deleted_at = deleted_at
        for variant in photo.file_asset.variants:
            if variant.deleted_at is None:
                variant.deleted_at = deleted_at
    db.commit()
    return {
        "photo_id": photo.id,
        "deleted_at": deleted_at,
    }


def update_summer_feeding_task(
    db: Session,
    *,
    task_id: UUID,
    admin: User,
    payload: SummerFeedingTaskUpdateRequest,
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
        removal_time = _now()
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
                execution.cancelled_at = removal_time
                execution.cancelled_by = admin.id
                execution.cancel_reason = EXECUTION_REMOVED_CANCEL_REASON
                execution.remark = execution.remark or EXECUTION_REMOVED_CANCEL_REASON
        task.start_at = _start_of_day(execute_dates[0])
        task.deadline_at = _end_of_day(execute_dates[-1])
    if payload.photos is not None:
        for photo in task.photos:
            photo.deleted_at = _now()
        _add_task_photos(db, task=task, photos=payload.photos, uploaded_by=admin)

    now = _now()
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
    _normalize_task_lifecycle(task)
    db.commit()
    return {"task_id": task.id, "updated_at": task.updated_at}


def update_task_status(
    db: Session,
    *,
    task_id: UUID,
    admin: User,
    payload: TaskStatusUpdateRequest,
) -> dict:
    task = get_task_or_raise(db, task_id, include_private=True)
    task.status = payload.status
    now = _now()
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


def soft_delete_task(
    db: Session,
    *,
    task_id: UUID,
    admin: User,
) -> dict:
    task = get_task_or_raise(db, task_id, include_private=True)
    now = _now()
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
