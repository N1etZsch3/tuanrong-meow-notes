from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import APIError
from app.modules.auth.models import AdminOperationLog, User
from app.modules.map.models import MapPoint
from app.modules.map.service import associated_poi_payload, get_default_campus
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
    "completed": "已结束",
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


def _now() -> datetime:
    return datetime.now(tz=UTC)


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
        selectinload(Task.photos),
        selectinload(Task.execution_dates).selectinload(TaskExecutionDate.completed_user),
        selectinload(Task.activities).selectinload(TaskActivityLog.actor).selectinload(User.profile),
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
    active_dates = [item for item in execution_dates if item.deleted_at is None]
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


def _execution_payload(execution_date: TaskExecutionDate | None) -> dict | None:
    if execution_date is None:
        return None
    return {
        "execution_date_id": execution_date.id,
        "execute_date": execution_date.execute_date.isoformat(),
        "status": execution_date.status,
        "completed_by": _user_payload(execution_date.completed_user),
        "completed_at": execution_date.completed_at,
        "checkin_id": execution_date.checkin_id,
        "remark": execution_date.remark,
    }


def _next_execution(
    execution_dates: list[TaskExecutionDate],
    today: date | None = None,
) -> TaskExecutionDate | None:
    today = today or date.today()
    active_dates = sorted(
        (item for item in execution_dates if item.deleted_at is None),
        key=lambda item: item.execute_date,
    )
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
    current_date = current_date or date.today()
    active_dates = sorted(
        (item for item in execution_dates if item.deleted_at is None),
        key=lambda item: item.execute_date,
    )
    exact = next((item for item in active_dates if item.execute_date == current_date), None)
    if exact:
        return exact
    fallback = active_dates[-1] if active_dates else None
    return _next_execution(active_dates, today=current_date) or fallback


def _photo_payload(photo: TaskPhoto) -> dict:
    return {
        "photo_id": photo.id,
        "file_id": photo.file_id,
        "file_url": photo.file_url,
        "thumbnail_url": photo.thumbnail_url,
        "cos_object_key": photo.cos_object_key,
        "photo_type": photo.photo_type,
        "caption": photo.caption,
        "sort_order": photo.sort_order,
        "is_cover": photo.is_cover,
        "created_at": photo.created_at,
    }


def _cover_photo_url(task: Task) -> str | None:
    photos = [photo for photo in task.photos if photo.deleted_at is None]
    cover = next((photo for photo in photos if photo.is_cover), None)
    if cover:
        return cover.thumbnail_url or cover.file_url
    first_photo = min(photos, key=lambda item: item.sort_order, default=None)
    return (first_photo.thumbnail_url or first_photo.file_url) if first_photo else None


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


def task_list_item_payload(task: Task) -> dict:
    current_execution = _current_execution(task.execution_dates)
    next_execution = _next_execution(task.execution_dates)
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
        "current_execution": _execution_payload(current_execution),
        "next_execution": _execution_payload(next_execution),
        "distance_meters": None,
        "published_at": task.published_at,
    }


def task_detail_payload(
    task: Task,
    *,
    current_date: date | None = None,
    activity_limit: int = 20,
    can_admin_edit: bool = False,
) -> dict:
    current_execution = _current_execution(task.execution_dates, current_date=current_date)
    next_execution = _next_execution(task.execution_dates, today=current_date)
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
        "current_execution": _execution_payload(current_execution),
        "next_execution": _execution_payload(next_execution),
        "map_point": _map_point_payload(task.map_point),
        "photos": [
            _photo_payload(photo)
            for photo in sorted(task.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None
        ],
        "execution_dates": [
            _execution_payload(item)
            for item in sorted(task.execution_dates, key=lambda item: item.execute_date)
            if item.deleted_at is None
        ],
        "activities": [
            _activity_payload(activity)
            for activity in sorted(task.activities, key=lambda item: item.created_at, reverse=True)[
                :activity_limit
            ]
        ],
        "actions": {
            "can_navigate": True,
            "can_checkin": task.status == "in_progress"
            and bool(current_execution)
            and current_execution.status == "pending",
            "checkin_disabled_reason": None
            if task.status == "in_progress"
            else "任务当前状态不可完成",
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
    statement = _task_statement_for_list(include_private=include_private)
    if status:
        statuses = [item.strip() for item in status.split(",") if item.strip()]
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
    query_date = date.today() if only_today else execute_date
    if query_date:
        task_ids = select(TaskExecutionDate.task_id).where(
            TaskExecutionDate.execute_date == query_date,
            TaskExecutionDate.deleted_at.is_(None),
        )
        statement = statement.where(Task.id.in_(task_ids))

    tasks = db.scalars(statement.order_by(Task.start_at.asc(), Task.published_at.desc())).all()
    total = len(tasks)
    start = (page - 1) * page_size
    paged = tasks[start : start + page_size]
    return {
        "items": [task_list_item_payload(task) for task in paged],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": start + page_size < total,
    }


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
        if not photo.file_url:
            raise APIError(
                code=TASK_ERROR_PHOTO_INVALID,
                message="任务图片参数不合法",
                status_code=400,
            )
        is_cover = photo.is_cover or (index == 0 and not cover_exists)
        task_photo = TaskPhoto(
            task_id=task.id,
            file_id=photo.file_id,
            file_url=photo.file_url,
            thumbnail_url=photo.thumbnail_url,
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
    include_private: bool = False,
    activity_limit: int = 20,
    can_admin_edit: bool = False,
) -> dict:
    task = get_task_or_raise(db, task_id, include_private=include_private)
    return task_detail_payload(
        task,
        current_date=current_date,
        activity_limit=activity_limit,
        can_admin_edit=can_admin_edit,
    )


def _checkin_photo(
    db: Session,
    *,
    task_id: UUID,
    checkin_id: UUID,
    photo: UploadedFileRef,
    uploaded_by: User,
    sort_order: int,
) -> None:
    db.add(
        TaskCheckinPhoto(
            checkin_id=checkin_id,
            task_id=task_id,
            file_id=photo.file_id,
            file_url=photo.file_url,
            thumbnail_url=photo.thumbnail_url,
            sort_order=sort_order,
            uploaded_by=uploaded_by.id,
        )
    )


def checkin_task(
    db: Session,
    *,
    task_id: UUID,
    user: User,
    payload: TaskCheckinRequest,
) -> dict:
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

    execute_date = payload.execute_date or date.today()
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
    for index, photo in enumerate(payload.photos):
        _checkin_photo(
            db,
            task_id=task.id,
            checkin_id=checkin.id,
            photo=photo,
            uploaded_by=user,
            sort_order=index,
        )

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
    db.add(
        TaskActivityLog(
            task_id=task.id,
            task_execution_date_id=execution.id,
            activity_type="execution_completed",
            title=f"第{sequence}次任务完成",
            content=f"{nickname} 于 {execute_date.isoformat()} 完成投喂",
            actor_id=user.id,
            activity_metadata={
                "execute_date": execute_date.isoformat(),
                "completed_at": now.isoformat(),
                "checkin_id": str(checkin.id),
            },
            created_at=now,
        )
    )
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
            "photos": [],
        },
    }


def update_summer_feeding_task(
    db: Session,
    *,
    task_id: UUID,
    admin: User,
    payload: SummerFeedingTaskUpdateRequest,
) -> dict:
    task = get_task_or_raise(db, task_id, include_private=True)
    if task.status not in {"in_progress", "completed"}:
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
                db.add(
                    TaskExecutionDate(
                        task_id=task.id,
                        execute_date=execute_date,
                        status="pending",
                    )
                )
        for execute_date, execution in existing.items():
            if execute_date not in execute_dates and execution.status != "completed":
                execution.status = "cancelled"
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
    if payload.status == "completed":
        task.completed_at = now
    task.updated_at = now
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
