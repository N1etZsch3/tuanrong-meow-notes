"""ORM → response payload assembly for tasks.

Presenters are pure: they never query the database. Callers must pass fully loaded ORM
objects (see loaders.py) and, for anything time-dependent, an explicit ``today``.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from app.core.errors import APIError
from app.modules.auth.models import User
from app.modules.map.models import MapPoint
from app.modules.map.service import associated_poi_payload
from app.modules.tasks.constants import (
    LOCAL_TZ,
    TASK_ERROR_EXECUTION_NOT_FOUND,
    TASK_STATUS_LABELS,
)
from app.modules.tasks.execution_state import (
    active_execution,
    active_execution_dates,
    execution_display_status,
    execution_display_status_label,
)
from app.modules.tasks.models import (
    Task,
    TaskActivityLog,
    TaskCheckin,
    TaskCheckinPhoto,
    TaskExecutionDate,
    TaskPhoto,
)
from app.modules.tasks.permissions import can_delete_checkin_photo


def _fallback_today() -> date:
    return datetime.now(tz=UTC).astimezone(LOCAL_TZ).date()


def split_statuses(value: str | None) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()] if value else []


def user_payload(user: User | None) -> dict | None:
    if user is None:
        return None
    return {
        "user_id": user.id,
        "nickname": user.profile.nickname if user.profile else user.student_no,
        "avatar_url": user.profile.avatar_url if user.profile else None,
    }


def date_range_payload(execution_dates: list[TaskExecutionDate]) -> dict:
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


def execution_payload(
    execution_date: TaskExecutionDate | None,
    *,
    today: date | None = None,
) -> dict | None:
    if execution_date is None:
        return None
    display_status = execution_display_status(execution_date, today=today or _fallback_today())
    return {
        "execution_date_id": execution_date.id,
        "execute_date": execution_date.execute_date.isoformat(),
        "status": execution_date.status,
        "display_status": display_status,
        "display_status_label": execution_display_status_label(display_status),
        "completed_by": user_payload(execution_date.completed_user),
        "completed_at": execution_date.completed_at,
        "checkin_id": execution_date.checkin_id,
        "remark": execution_date.remark,
    }


def next_execution(
    execution_dates: list[TaskExecutionDate],
    today: date | None = None,
) -> TaskExecutionDate | None:
    today = today or _fallback_today()
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


def current_execution(
    execution_dates: list[TaskExecutionDate],
    current_date: date | None = None,
) -> TaskExecutionDate | None:
    current_date = current_date or _fallback_today()
    return active_execution(execution_dates, today=current_date)


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


def execution_matches_filters(
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


def display_executions_payload(
    execution_dates: list[TaskExecutionDate],
    *,
    execute_date: date | None = None,
    execute_date_start: date | None = None,
    execute_date_end: date | None = None,
    execution_status: str | None = None,
    execution_display_status: str | None = None,
    today: date,
) -> list[dict]:
    storage_statuses = set(split_statuses(execution_status))
    display_statuses = set(split_statuses(execution_display_status))
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
            if execution_matches_filters(
                item,
                execute_date=execute_date,
                execute_date_start=execute_date_start,
                execute_date_end=execute_date_end,
                execution_statuses=storage_statuses,
                execution_display_statuses=display_statuses,
                today=today,
            )
        ]
    return [execution_payload(item, today=today) for item in active_dates]


def list_display_execution(
    execution_dates: list[TaskExecutionDate],
    *,
    execute_date: date | None = None,
    execute_date_start: date | None = None,
    execute_date_end: date | None = None,
    execution_status: str | None = None,
    execution_display_status: str | None = None,
    today: date | None = None,
) -> TaskExecutionDate | None:
    today = today or _fallback_today()
    active_dates = active_execution_dates(execution_dates)
    statuses = set(split_statuses(execution_status))
    display_statuses = set(split_statuses(execution_display_status))
    has_execution_filter = bool(
        execute_date or execute_date_start or execute_date_end or statuses or display_statuses
    )
    if not has_execution_filter:
        return current_execution(active_dates, current_date=today)

    matching = [
        item
        for item in active_dates
        if execution_matches_filters(
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
        return current_execution(active_dates, current_date=today)

    upcoming = [item for item in matching if item.execute_date >= today]
    return upcoming[0] if upcoming else matching[-1]


def asset_backed_photo_urls(photo: TaskPhoto | TaskCheckinPhoto) -> tuple[str, str | None]:
    asset = getattr(photo, "file_asset", None)
    if asset is not None and asset.deleted_at is None:
        return (
            asset.default_url or photo.file_url,
            asset.default_thumb_url or photo.thumbnail_url,
        )
    return photo.file_url, photo.thumbnail_url


def photo_payload(photo: TaskPhoto) -> dict:
    file_url, thumbnail_url = asset_backed_photo_urls(photo)
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


def checkin_photo_payload(photo: TaskCheckinPhoto, viewer: User | None) -> dict:
    file_url, thumbnail_url = asset_backed_photo_urls(photo)
    return {
        "photo_id": photo.id,
        "checkin_id": photo.checkin_id,
        "task_id": photo.task_id,
        "file_id": photo.file_id,
        "file_url": file_url,
        "thumbnail_url": thumbnail_url,
        "caption": photo.caption,
        "sort_order": photo.sort_order,
        "uploaded_by": user_payload(photo.uploader),
        "can_delete": can_delete_checkin_photo(photo, viewer),
        "created_at": photo.created_at,
    }


def task_checkin_photos_payload(
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
        checkin_photo_payload(photo, viewer)
        for _, _, photo in ordered_photos
    ]


def checkin_record_payload(checkin: TaskCheckin, viewer: User | None) -> dict:
    return {
        "checkin_id": checkin.id,
        "task_execution_date_id": checkin.task_execution_date_id,
        "execute_date": checkin.execute_date,
        "submitter": user_payload(checkin.submitter),
        "is_completed": checkin.is_completed,
        "process_result": checkin.process_result,
        "remark": checkin.remark,
        "submitted_at": checkin.submitted_at,
        "photos": [
            checkin_photo_payload(photo, viewer)
            for photo in sorted(checkin.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None
        ],
    }


def task_checkins_payload(
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
    return [checkin_record_payload(checkin, viewer) for checkin in checkins]


def activities_payload(
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
    return [activity_payload(activity) for activity in filtered]


def execution_groups_payload(
    task: Task,
    *,
    viewer: User | None,
    today: date,
) -> list[dict]:
    return [
        {
            "execution": execution_payload(execution, today=today),
            "activities": activities_payload(
                task.activities,
                execution_date_id=execution.id,
            ),
            "checkin_photos": task_checkin_photos_payload(
                task,
                viewer,
                execution_date_id=execution.id,
            ),
        }
        for execution in active_execution_dates(task.execution_dates)
    ]


def cover_photo_url(task: Task) -> str | None:
    photos = [photo for photo in task.photos if photo.deleted_at is None]
    cover = next((photo for photo in photos if photo.is_cover), None)
    if cover:
        file_url, thumbnail_url = asset_backed_photo_urls(cover)
        return thumbnail_url or file_url
    first_photo = min(photos, key=lambda item: item.sort_order, default=None)
    if first_photo is None:
        return None
    file_url, thumbnail_url = asset_backed_photo_urls(first_photo)
    return thumbnail_url or file_url


def map_point_payload(point: MapPoint) -> dict:
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


def activity_payload(activity: TaskActivityLog) -> dict:
    execute_date = None
    if activity.activity_metadata:
        execute_date = activity.activity_metadata.get("execute_date")
    return {
        "activity_id": activity.id,
        "activity_type": activity.activity_type,
        "title": activity.title,
        "content": activity.content,
        "actor": user_payload(activity.actor),
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
    today = today or _fallback_today()
    current = list_display_execution(
        task.execution_dates,
        execute_date=execute_date,
        execute_date_start=execute_date_start,
        execute_date_end=execute_date_end,
        execution_status=execution_status,
        execution_display_status=execution_display_status,
        today=today,
    )
    upcoming = next_execution(task.execution_dates, today=today)
    display_executions = display_executions_payload(
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
        "cover_photo_url": cover_photo_url(task),
        "map_point": {
            "map_point_id": task.map_point.id,
            "location_name": task.map_point.location_name,
            "location_detail": task.map_point.location_detail,
            "lng": float(task.map_point.lng),
            "lat": float(task.map_point.lat),
        },
        "date_range": date_range_payload(task.execution_dates),
        "current_execution": execution_payload(current, today=today),
        "next_execution": execution_payload(upcoming, today=today),
        "display_executions": display_executions,
        "distance_meters": None,
        "published_at": task.published_at,
    }


def checkin_disabled_reason(
    task: Task,
    current: TaskExecutionDate | None,
    *,
    today: date,
) -> str | None:
    if task.status != "in_progress":
        return "任务当前状态不可完成"
    if current is None:
        return "暂无执行日期"
    if current.status == "completed":
        return "该日期已完成"
    if current.status not in {"pending", "missed"}:
        return "该日期不可完成"
    if current.execute_date > today:
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
    today = current_date or _fallback_today()
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
    current = selected_execution or current_execution(
        task.execution_dates,
        current_date=today,
    )
    upcoming = next_execution(task.execution_dates, today=today)
    disabled_reason = checkin_disabled_reason(
        task,
        current,
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
        "date_range": date_range_payload(task.execution_dates),
        "current_execution": execution_payload(current, today=today),
        "next_execution": execution_payload(upcoming, today=today),
        "display_executions": display_executions_payload(task.execution_dates, today=today),
        "detail_scope": "execution" if selected_execution is not None else "parent",
        "active_execution_id": current.id if current is not None else None,
        "execution": (
            execution_payload(selected_execution, today=today)
            if selected_execution is not None
            else None
        ),
        "map_point": map_point_payload(task.map_point),
        "photos": [
            photo_payload(photo)
            for photo in sorted(task.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None
        ],
        "checkin_photos": task_checkin_photos_payload(
            task,
            viewer,
            execution_date_id=scoped_execution_id,
        ),
        "checkins": task_checkins_payload(
            task,
            viewer,
            execution_date_id=scoped_execution_id,
        ),
        "execution_dates": [
            execution_payload(item, today=today)
            for item in sorted(task.execution_dates, key=lambda item: item.execute_date)
            if item.deleted_at is None
        ],
        "execution_groups": execution_groups_payload(task, viewer=viewer, today=today),
        "activities": activities_payload(
            task.activities,
            execution_date_id=scoped_execution_id,
            limit=activity_limit,
        ),
        "actions": {
            "can_navigate": True,
            "can_checkin": disabled_reason is None,
            "checkin_disabled_reason": disabled_reason,
            "can_admin_edit": can_admin_edit,
        },
        "published_at": task.published_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }
