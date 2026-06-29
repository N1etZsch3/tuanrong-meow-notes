from datetime import date
from math import asin, cos, radians, sin, sqrt
from urllib.parse import quote
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.errors import APIError, ErrorCode
from app.modules.map.models import Campus, CampusArea, MapMarkerConfig, MapPoint, MapPointPhoto
from app.modules.tasks.models import Task

EARTH_RADIUS_METERS = 6_371_000


def as_float(value) -> float | None:
    if value is None:
        return None
    return float(value)


def parse_csv_filter(value: str | None) -> set[str] | None:
    if not value:
        return None
    values = {item.strip() for item in value.split(",") if item.strip()}
    return values or None


def distance_meters(
    *,
    from_lng: float | None,
    from_lat: float | None,
    to_lng: float,
    to_lat: float,
) -> int | None:
    if from_lng is None or from_lat is None:
        return None
    lng1, lat1, lng2, lat2 = map(radians, [from_lng, from_lat, to_lng, to_lat])
    delta_lng = lng2 - lng1
    delta_lat = lat2 - lat1
    haversine = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lng / 2) ** 2
    return round(2 * EARTH_RADIUS_METERS * asin(sqrt(haversine)))


def get_default_campus(db: Session, campus_id: UUID | None = None) -> Campus:
    statement = select(Campus).where(Campus.is_active.is_(True))
    if campus_id:
        statement = statement.where(Campus.id == campus_id)
    campus = db.scalar(statement.order_by(Campus.created_at.asc()).limit(1))
    if campus is None:
        raise APIError(
            code=ErrorCode.MAP_CAMPUS_NOT_FOUND,
            message="校园配置不存在",
            status_code=404,
        )
    return campus


def marker_configs_by_key(db: Session) -> dict[str, MapMarkerConfig]:
    configs = db.scalars(select(MapMarkerConfig).order_by(MapMarkerConfig.sort_order.asc())).all()
    return {config.marker_key: config for config in configs}


def campus_payload(campus: Campus) -> dict:
    return {
        "campus_id": campus.id,
        "name": campus.name,
        "center_lng": as_float(campus.center_lng),
        "center_lat": as_float(campus.center_lat),
        "default_zoom": campus.default_zoom,
        "min_zoom": campus.min_zoom,
        "max_zoom": campus.max_zoom,
        "boundary": None,
    }


def area_payload(area: CampusArea) -> dict:
    return {
        "area_id": area.id,
        "parent_id": area.parent_id,
        "name": area.name,
        "area_type": area.area_type,
        "center_lng": as_float(area.center_lng),
        "center_lat": as_float(area.center_lat),
        "sort_order": area.sort_order,
    }


def marker_config_payload(config: MapMarkerConfig) -> dict:
    return {
        "marker_key": config.marker_key,
        "point_type": config.point_type,
        "business_type": config.business_type,
        "label": config.label,
        "icon_url": config.icon_url,
        "icon_svg": config.icon_svg,
        "color": config.color,
        "z_index": config.z_index,
        "default_visible": config.default_visible,
        "default_label_min_zoom": config.default_label_min_zoom,
        "default_preview_min_zoom": config.default_preview_min_zoom,
        "default_preview_enabled": config.default_preview_enabled,
        "icon_width": config.icon_width,
        "icon_height": config.icon_height,
        "anchor_x": config.anchor_x,
        "anchor_y": config.anchor_y,
    }


def point_cover_photo(point: MapPoint) -> str | None:
    photos = [photo for photo in point.photos if photo.deleted_at is None]
    cover = next((photo for photo in photos if photo.photo_type == "cover"), None)
    if cover:
        return cover.thumbnail_url or cover.file_url
    first_photo = min(photos, key=lambda photo: photo.sort_order, default=None)
    if first_photo is None:
        return None
    return first_photo.thumbnail_url or first_photo.file_url


def point_business_type(point: MapPoint, configs: dict[str, MapMarkerConfig]) -> str | None:
    if point.icon_key and point.icon_key in configs:
        return configs[point.icon_key].business_type
    return None


def point_marker_key(point: MapPoint) -> str | None:
    return point.icon_key


def task_by_map_point_ids(db: Session, points: list[MapPoint]) -> dict[UUID, Task]:
    point_ids = [point.id for point in points if point.point_type == "task"]
    if not point_ids:
        return {}
    tasks = db.scalars(
        select(Task)
        .options(selectinload(Task.execution_dates))
        .where(Task.map_point_id.in_(point_ids), Task.deleted_at.is_(None))
    ).all()
    return {task.map_point_id: task for task in tasks}


def next_task_execution_date(task: Task) -> str | None:
    today = date.today()
    active_dates = sorted(
        (item for item in task.execution_dates if item.deleted_at is None),
        key=lambda item: item.execute_date,
    )
    pending = [
        item
        for item in active_dates
        if item.status == "pending" and item.execute_date >= today
    ]
    if pending:
        return pending[0].execute_date.isoformat()
    fallback = next((item for item in active_dates if item.status == "pending"), None)
    return fallback.execute_date.isoformat() if fallback else None


def today_task_execution_status(task: Task) -> str | None:
    today = date.today()
    execution = next(
        (
            item
            for item in task.execution_dates
            if item.deleted_at is None and item.execute_date == today
        ),
        None,
    )
    return execution.status if execution else None


def task_marker_extra(task: Task | None) -> dict:
    if task is None:
        return {}
    return {
        "task_status": task.status,
        "next_execute_date": next_task_execution_date(task),
        "today_status": today_task_execution_status(task),
    }


def point_label(point: MapPoint, configs: dict[str, MapMarkerConfig]) -> str:
    if point.icon_key and point.icon_key in configs:
        return configs[point.icon_key].label
    labels = {
        "task": "任务点",
        "cat": "猫咪点",
        "supply": "物资点",
        "landmark": "地标",
    }
    return labels.get(point.point_type, point.point_type)


def point_marker_payload(
    point: MapPoint,
    configs: dict[str, MapMarkerConfig],
    *,
    user_lng: float | None = None,
    user_lat: float | None = None,
    task: Task | None = None,
) -> dict:
    lng = as_float(point.lng)
    lat = as_float(point.lat)
    return {
        "point_id": point.id,
        "point_type": point.point_type,
        "point_scope": point.point_scope,
        "business_type": point_business_type(point, configs),
        "business_id": task.id if task else point.id,
        "name": point.name,
        "subtitle": point.subtitle,
        "lng": lng,
        "lat": lat,
        "area_id": point.area_id,
        "area_name": point.area.name if point.area else None,
        "marker_key": point_marker_key(point),
        "icon_key": point.icon_key,
        "display_level": point.display_level,
        "visibility": point.visibility,
        "status": point.status,
        "cover_photo_url": point_cover_photo(point),
        "preview_enabled": point.preview_enabled,
        "preview_min_zoom": point.preview_min_zoom,
        "label_min_zoom": point.label_min_zoom,
        "distance_meters": distance_meters(
            from_lng=user_lng,
            from_lat=user_lat,
            to_lng=lng,
            to_lat=lat,
        ),
        "extra": task_marker_extra(task),
    }


def map_init(db: Session, campus_id: UUID | None = None) -> dict:
    campus = get_default_campus(db, campus_id)
    settings = get_settings()
    areas = db.scalars(
        select(CampusArea)
        .where(CampusArea.campus_id == campus.id, CampusArea.is_visible.is_(True))
        .order_by(CampusArea.sort_order.asc(), CampusArea.name.asc())
    ).all()
    marker_configs = db.scalars(
        select(MapMarkerConfig)
        .where(MapMarkerConfig.default_visible.is_(True))
        .order_by(MapMarkerConfig.sort_order.asc(), MapMarkerConfig.z_index.desc())
    ).all()
    return {
        "campus": campus_payload(campus),
        "areas": [area_payload(area) for area in areas],
        "marker_configs": [marker_config_payload(config) for config in marker_configs],
        "default_filters": {
            "point_types": ["task", "cat", "supply", "landmark"],
            "include_hidden": False,
            "only_available_tasks": False,
        },
        "ui_config": {
            "show_title": True,
            "search_placeholder": "搜索猫咪、任务、物资点、地标",
            "bottom_default_mode": "auto",
        },
        "amap_config": {
            "web_key": settings.amap_web_key,
            "security_js_code": settings.amap_security_js_code,
            "map_style": "amap://styles/fresh",
        },
    }


def visible_points_statement():
    return (
        select(MapPoint)
        .options(selectinload(MapPoint.area), selectinload(MapPoint.photos))
        .where(
            MapPoint.status == "active",
            MapPoint.visibility == "public",
            MapPoint.deleted_at.is_(None),
        )
    )


def map_points(
    db: Session,
    *,
    campus_id: UUID | None = None,
    point_types: str | None = None,
    business_types: str | None = None,
    area_id: UUID | None = None,
    min_lng: float | None = None,
    min_lat: float | None = None,
    max_lng: float | None = None,
    max_lat: float | None = None,
    user_lng: float | None = None,
    user_lat: float | None = None,
) -> dict:
    campus = get_default_campus(db, campus_id)
    configs = marker_configs_by_key(db)
    type_filter = parse_csv_filter(point_types)
    business_filter = parse_csv_filter(business_types)
    statement = visible_points_statement().where(MapPoint.campus_id == campus.id)
    if type_filter:
        statement = statement.where(MapPoint.point_type.in_(type_filter))
    if area_id:
        statement = statement.where(MapPoint.area_id == area_id)
    if min_lng is not None and max_lng is not None:
        statement = statement.where(MapPoint.lng >= min_lng, MapPoint.lng <= max_lng)
    if min_lat is not None and max_lat is not None:
        statement = statement.where(MapPoint.lat >= min_lat, MapPoint.lat <= max_lat)

    points = db.scalars(
        statement.order_by(MapPoint.display_level.desc(), MapPoint.created_at.desc())
    ).all()
    if business_filter:
        points = [
            point
            for point in points
            if point_business_type(point, configs) in business_filter
        ]
    task_lookup = task_by_map_point_ids(db, points)
    return {
        "items": [
            point_marker_payload(
                point,
                configs,
                user_lng=user_lng,
                user_lat=user_lat,
                task=task_lookup.get(point.id),
            )
            for point in points
        ],
        "total": len(points),
        "map_strategy": {
            "cluster_enabled": False,
            "label_collision": "frontend",
            "max_marker_count": 200,
        },
    }


def normalized_search_text(point: MapPoint) -> str:
    values = [
        point.name,
        point.subtitle,
        point.description,
        point.location_name,
        point.location_detail,
        point.route_instruction,
        point.landmark_hint,
        point.entrance_hint,
        point.amap_address,
    ]
    return " ".join(value for value in values if value).lower()


def search(
    db: Session,
    *,
    keyword: str,
    campus_id: UUID | None = None,
    point_types: str | None = None,
    user_lng: float | None = None,
    user_lat: float | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        raise APIError(
            code=ErrorCode.MAP_SEARCH_KEYWORD_EMPTY,
            message="搜索关键词不能为空",
            status_code=400,
        )
    if len(normalized_keyword) > 50:
        raise APIError(
            code=ErrorCode.MAP_SEARCH_KEYWORD_TOO_LONG,
            message="搜索关键词过长",
            status_code=400,
        )

    campus = get_default_campus(db, campus_id)
    configs = marker_configs_by_key(db)
    type_filter = parse_csv_filter(point_types)
    keyword_lower = normalized_keyword.lower()
    matched = []
    statement = visible_points_statement().where(MapPoint.campus_id == campus.id)
    if type_filter:
        statement = statement.where(MapPoint.point_type.in_(type_filter))
    points = db.scalars(statement).all()
    points_by_id = {point.id: point for point in points}
    task_lookup = task_by_map_point_ids(db, points)
    for point in points:
        text = normalized_search_text(point)
        if keyword_lower not in text:
            continue
        payload = point_marker_payload(
            point,
            configs,
            user_lng=user_lng,
            user_lat=user_lat,
            task=task_lookup.get(point.id),
        )
        exact_title_bonus = 1000 if keyword_lower == point.name.lower() else 0
        title_bonus = 100 if keyword_lower in point.name.lower() else 0
        payload["sort_score"] = point.display_level + exact_title_bonus + title_bonus
        matched.append(payload)

    matched.sort(key=lambda item: item["sort_score"], reverse=True)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    start = (page - 1) * page_size
    items = matched[start : start + page_size]
    return {
        "items": [
            {
                "result_type": item["point_type"],
                "map_point_id": item["point_id"],
                "business_id": item["business_id"],
                "point_type": item["point_type"],
                "business_type": item["business_type"],
                "title": item["name"],
                "subtitle": item["subtitle"],
                "description": points_by_id[item["point_id"]].description,
                "icon_key": item["icon_key"],
                "cover_photo_url": item["cover_photo_url"],
                "lng": item["lng"],
                "lat": item["lat"],
                "distance_meters": item["distance_meters"],
                "status_label": point_label_for_type(item["point_type"], item["business_type"]),
                "highlight_text": normalized_keyword,
                "sort_score": item["sort_score"],
            }
            for item in items
        ],
        "page": page,
        "page_size": page_size,
        "total": len(matched),
        "has_more": start + page_size < len(matched),
        "suggestions": [] if matched else ["北门", "小橘", "猫粮", "体育馆"],
    }


def point_label_for_type(point_type: str, business_type: str | None) -> str:
    if point_type == "task" and business_type == "emergency":
        return "紧急任务"
    if point_type == "task" and business_type == "feeding":
        return "喂食任务"
    if point_type == "task":
        return "日常任务"
    if point_type == "cat":
        return "猫咪点"
    if point_type == "supply":
        return "物资点"
    if point_type == "landmark":
        return "地标"
    return point_type


def get_visible_point(db: Session, point_id: UUID) -> MapPoint:
    point = db.scalar(visible_points_statement().where(MapPoint.id == point_id))
    if point is None:
        raise APIError(
            code=ErrorCode.MAP_POINT_NOT_FOUND,
            message="点位不存在",
            status_code=404,
        )
    return point


def photo_payload(photo: MapPointPhoto) -> dict:
    return {
        "photo_id": photo.id,
        "photo_type": photo.photo_type,
        "file_url": photo.file_url,
        "thumbnail_url": photo.thumbnail_url,
        "caption": photo.caption,
        "sort_order": photo.sort_order,
        "created_at": photo.created_at,
    }


def summary(
    db: Session,
    *,
    point_id: UUID,
    user_lng: float | None = None,
    user_lat: float | None = None,
) -> dict:
    point = get_visible_point(db, point_id)
    configs = marker_configs_by_key(db)
    task = task_by_map_point_ids(db, [point]).get(point.id)
    lng = as_float(point.lng)
    lat = as_float(point.lat)
    business_type = point_business_type(point, configs)
    tags = [point_label(point, configs), point_label_for_type(point.point_type, business_type)]
    return {
        "point_id": point.id,
        "point_type": point.point_type,
        "business_type": business_type,
        "business_id": task.id if task else point.id,
        "title": point.name,
        "subtitle": point.subtitle,
        "cover_photo_url": point_cover_photo(point),
        "tags": list(dict.fromkeys(tag for tag in tags if tag)),
        "description": point.description,
        "location_name": point.location_name,
        "location_detail": point.location_detail,
        "route_instruction": point.route_instruction,
        "landmark_hint": point.landmark_hint,
        "entrance_hint": point.entrance_hint,
        "lng": lng,
        "lat": lat,
        "distance_meters": distance_meters(
            from_lng=user_lng,
            from_lat=user_lat,
            to_lng=lng,
            to_lat=lat,
        ),
        "photos": [
            photo_payload(photo)
            for photo in sorted(point.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None
        ],
        "business_summary": task_marker_extra(task),
        "actions": [
            {
                "key": "navigate",
                "label": "导航",
                "enabled": True,
                "disabled_reason": None,
                "method": "GET",
                "path": f"/api/v1/map/points/{point.id}/navigation",
                "target_type": "api",
            },
            {
                "key": "view_detail",
                "label": "查看详情",
                "enabled": True,
                "disabled_reason": None,
                "method": None,
                "path": detail_path(point, task),
                "target_type": "page",
            },
        ],
    }


def detail_path(point: MapPoint, task: Task | None = None) -> str:
    if point.point_type == "task":
        if task:
            return f"/pages/tasks/detail?task_id={task.id}"
        return f"/pages/tasks/detail?map_point_id={point.id}"
    if point.point_type == "cat":
        return f"/pages/cats/detail?map_point_id={point.id}"
    if point.point_type == "supply":
        return f"/pages/supplies/detail?map_point_id={point.id}"
    return f"/pages/map/points/detail?point_id={point.id}"


def navigation(db: Session, *, point_id: UUID) -> dict:
    point = get_visible_point(db, point_id)
    lng = as_float(point.lng)
    lat = as_float(point.lat)
    title = point.location_name or point.name
    encoded_title = quote(title)
    return {
        "point_id": point.id,
        "title": point.name,
        "destination": {
            "lng": lng,
            "lat": lat,
            "location_name": title,
            "amap_poi_id": point.amap_poi_id,
            "amap_address": point.amap_address,
        },
        "route_instruction": point.route_instruction,
        "landmark_hint": point.landmark_hint,
        "entrance_hint": point.entrance_hint,
        "photos": [
            photo_payload(photo)
            for photo in sorted(point.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None and photo.photo_type in {"route", "entrance", "scene"}
        ],
        "amap_navigation": {
            "mode": "walking",
            "open_url": f"amapuri://route/plan/?dlat={lat}&dlon={lng}&dev=0&t=2",
            "web_url": f"https://uri.amap.com/navigation?to={lng},{lat},{encoded_title}&mode=walk",
        },
    }


def bottom_content(db: Session, *, mode: str = "auto", limit: int = 10) -> dict:
    configs = marker_configs_by_key(db)
    statement = (
        visible_points_statement()
        .where(MapPoint.point_type == "task")
        .order_by(MapPoint.display_level.desc(), MapPoint.created_at.desc())
        .limit(limit)
    )
    points = db.scalars(statement).all()
    task_lookup = task_by_map_point_ids(db, points)
    return {
        "content_type": "latest_tasks" if mode == "auto" else mode,
        "title": "最新任务",
        "items": [
            {
                "id": task_lookup[point.id].id if point.id in task_lookup else point.id,
                "type": "emergency_task"
                if point_business_type(point, configs) == "emergency"
                else "daily_task",
                "title": task_lookup[point.id].title if point.id in task_lookup else point.name,
                "subtitle": point.subtitle,
                "description": task_lookup[point.id].description
                if point.id in task_lookup
                else point.description,
                "distance_meters": None,
                "status_label": point_label_for_type(
                    point.point_type,
                    point_business_type(point, configs),
                ),
                "tag_label": point_label(point, configs),
                "map_point_id": point.id,
            }
            for point in points
        ],
    }
