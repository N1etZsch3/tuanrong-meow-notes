import json
from datetime import date
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt
from urllib.parse import quote, urlencode
from urllib.request import urlopen
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.errors import APIError, ErrorCode
from app.modules.auth.models import User
from app.modules.map.models import Campus, CampusArea, MapMarkerConfig, MapPoint, MapPointPhoto
from app.modules.tasks.models import Task

EARTH_RADIUS_METERS = 6_371_000
AMAP_REST_BASE_URL = "https://restapi.amap.com"


def as_float(value) -> float | None:
    if value is None:
        return None
    return float(value)


def parse_csv_filter(value: str | None) -> set[str] | None:
    if not value:
        return None
    values = {item.strip() for item in value.split(",") if item.strip()}
    return values or None


def format_coord(value: float | Decimal | None) -> str:
    if value is None:
        return ""
    return f"{float(value):.7f}".rstrip("0").rstrip(".")


def point_wkt(lng: float | Decimal, lat: float | Decimal) -> str:
    return f"POINT({float(lng):.7f} {float(lat):.7f})"


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


def _request_amap_json(path: str, params: dict) -> dict:
    settings = get_settings()
    key = settings.effective_amap_web_service_key
    if not key:
        return {}
    query = {**params, "key": key}
    url = f"{AMAP_REST_BASE_URL}{path}?{urlencode(query)}"
    with urlopen(url, timeout=settings.amap_web_service_timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_lng_lat_pair(value: str | None) -> tuple[float, float] | None:
    if not value:
        return None
    try:
        lng_text, lat_text = value.split(",", 1)
        return float(lng_text), float(lat_text)
    except (TypeError, ValueError):
        return None


def parse_amap_polyline(polyline: str | None) -> list[dict]:
    if not polyline:
        return []
    points = []
    for part in polyline.split(";"):
        parsed = parse_lng_lat_pair(part)
        if not parsed:
            continue
        lng, lat = parsed
        point = {"lng": lng, "lat": lat}
        if not points or points[-1] != point:
            points.append(point)
    return points


def fallback_route(
    *,
    from_lng: float | None,
    from_lat: float | None,
    to_lng: float,
    to_lat: float,
) -> dict:
    points = [{"lng": to_lng, "lat": to_lat}]
    if from_lng is not None and from_lat is not None:
        points.insert(0, {"lng": from_lng, "lat": from_lat})
    return {
        "provider": "fallback",
        "fallback": True,
        "distance_meters": distance_meters(
            from_lng=from_lng,
            from_lat=from_lat,
            to_lng=to_lng,
            to_lat=to_lat,
        ),
        "duration_seconds": None,
        "points": points,
        "steps": [],
    }


def build_walking_route(
    *,
    from_lng: float | None,
    from_lat: float | None,
    to_lng: float,
    to_lat: float,
) -> dict:
    if from_lng is None or from_lat is None:
        return fallback_route(from_lng=from_lng, from_lat=from_lat, to_lng=to_lng, to_lat=to_lat)

    try:
        payload = _request_amap_json(
            "/v3/direction/walking",
            {
                "origin": f"{format_coord(from_lng)},{format_coord(from_lat)}",
                "destination": f"{format_coord(to_lng)},{format_coord(to_lat)}",
                "output": "json",
            },
        )
    except Exception:
        return fallback_route(from_lng=from_lng, from_lat=from_lat, to_lng=to_lng, to_lat=to_lat)

    if payload.get("status") != "1":
        return fallback_route(from_lng=from_lng, from_lat=from_lat, to_lng=to_lng, to_lat=to_lat)
    paths = (payload.get("route") or {}).get("paths") or []
    if not paths:
        return fallback_route(from_lng=from_lng, from_lat=from_lat, to_lng=to_lng, to_lat=to_lat)

    path = paths[0]
    route_points: list[dict] = []
    steps = []
    for step in path.get("steps") or []:
        polyline_points = parse_amap_polyline(step.get("polyline"))
        for point in polyline_points:
            if not route_points or route_points[-1] != point:
                route_points.append(point)
        steps.append(
            {
                "instruction": step.get("instruction") or "",
                "distance_meters": int(float(step.get("distance") or 0)),
                "duration_seconds": int(float(step.get("duration") or 0)),
                "points": polyline_points,
            }
        )

    if not route_points:
        route_points = [
            {"lng": from_lng, "lat": from_lat},
            {"lng": to_lng, "lat": to_lat},
        ]

    return {
        "provider": "amap",
        "fallback": False,
        "distance_meters": int(float(path.get("distance") or 0)),
        "duration_seconds": int(float(path.get("duration") or 0)),
        "points": route_points,
        "steps": steps,
    }


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


def active_task_execution_dates(task: Task):
    return [item for item in task.execution_dates if item.deleted_at is None]


def feeding_task_marker_status(task: Task | None) -> str | None:
    if task is None or task.task_type != "feeding":
        return None
    today_status = today_task_execution_status(task)
    if today_status == "completed":
        return "completed"

    active_dates = active_task_execution_dates(task)
    if active_dates and all(item.status == "completed" for item in active_dates):
        return "completed"
    return "pending"


def task_marker_extra(task: Task | None) -> dict:
    if task is None:
        return {}
    extra = {
        "task_status": task.status,
        "next_execute_date": next_task_execution_date(task),
        "today_status": today_task_execution_status(task),
    }
    feeding_status = feeding_task_marker_status(task)
    if feeding_status:
        extra["feeding_status"] = feeding_status
    return extra


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
    configs_by_key = {config.marker_key: config for config in marker_configs}
    return {
        "campus": campus_payload(campus),
        "areas": [area_payload(area) for area in areas],
        "marker_configs": [marker_config_payload(config) for config in marker_configs],
        "filter_options": map_filter_options(db, campus=campus, configs=configs_by_key),
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


def map_filter_options(
    db: Session,
    *,
    campus: Campus,
    configs: dict[str, MapMarkerConfig],
) -> list[dict]:
    points = db.scalars(visible_points_statement().where(MapPoint.campus_id == campus.id)).all()
    task_lookup = task_by_map_point_ids(db, points)
    feeding_statuses = {
        status
        for point in points
        if point.point_type == "task" and point_business_type(point, configs) == "feeding"
        for status in [feeding_task_marker_status(task_lookup.get(point.id))]
        if status
    }
    options = [
        {
            "key": "none",
            "label": "无标记",
            "description": "暂不显示地图点位",
            "icon_key": "filter_none",
            "point_types": [],
            "business_types": [],
        }
    ]
    if "pending" in feeding_statuses:
        options.append(
            {
                "key": "feeding_pending",
                "label": "未完成任务",
                "description": "尚未完成的暑假投喂点",
                "icon_key": "feeding_pending",
                "point_types": ["task"],
                "business_types": ["feeding"],
            }
        )
    if "completed" in feeding_statuses:
        options.append(
            {
                "key": "feeding_completed",
                "label": "完成任务",
                "description": "已完成投喂的任务点",
                "icon_key": "feeding_completed",
                "point_types": ["task"],
                "business_types": ["feeding"],
            }
        )
    return options


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
    filter_key: str | None = None,
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
    normalized_filter_key = (filter_key or "").strip()
    if normalized_filter_key == "none":
        return {
            "items": [],
            "total": 0,
            "map_strategy": {
                "cluster_enabled": False,
                "label_collision": "frontend",
                "max_marker_count": 200,
            },
        }
    if normalized_filter_key in {"feeding_pending", "feeding_completed"}:
        point_types = "task"
        business_types = "feeding"
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
    if normalized_filter_key in {"feeding_pending", "feeding_completed"}:
        target_status = normalized_filter_key.replace("feeding_", "")
        points = [
            point
            for point in points
            if feeding_task_marker_status(task_lookup.get(point.id)) == target_status
        ]
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


def external_poi_search_results(
    *,
    keyword: str,
    campus: Campus,
    user_lng: float | None = None,
    user_lat: float | None = None,
    limit: int = 20,
) -> list[dict]:
    try:
        payload = _request_amap_json(
            "/v3/place/text",
            {
                "keywords": keyword,
                "city": "黄石",
                "citylimit": "false",
                "offset": str(min(max(limit, 1), 25)),
                "page": "1",
                "extensions": "base",
                "output": "json",
                "location": f"{format_coord(campus.center_lng)},{format_coord(campus.center_lat)}",
            },
        )
    except Exception:
        return []

    if payload.get("status") != "1":
        return []

    results = []
    for index, poi in enumerate(payload.get("pois") or []):
        parsed = parse_lng_lat_pair(poi.get("location"))
        if not parsed:
            continue
        lng, lat = parsed
        poi_id = poi.get("id") or f"{keyword}-{index}"
        distance = distance_meters(
            from_lng=user_lng,
            from_lat=user_lat,
            to_lng=lng,
            to_lat=lat,
        )
        results.append(
            {
                "result_type": "external_poi",
                "map_point_id": None,
                "business_id": f"amap:{poi_id}",
                "point_type": "landmark",
                "business_type": "amap_poi",
                "title": poi.get("name") or keyword,
                "subtitle": poi.get("type") or "高德地图点位",
                "description": poi.get("address") or None,
                "icon_key": "landmark",
                "cover_photo_url": None,
                "lng": lng,
                "lat": lat,
                "distance_meters": distance,
                "status_label": "地图点位",
                "highlight_text": keyword,
                "sort_score": 50 - index,
            }
        )
    return results


def search(
    db: Session,
    *,
    keyword: str,
    campus_id: UUID | None = None,
    point_types: str | None = None,
    include_external: bool = False,
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

    internal_items = [
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
        for item in matched
    ]
    external_items = (
        external_poi_search_results(
            keyword=normalized_keyword,
            campus=campus,
            user_lng=user_lng,
            user_lat=user_lat,
            limit=page_size,
        )
        if include_external and (not type_filter or "landmark" in type_filter)
        else []
    )
    all_items = [*internal_items, *external_items]
    all_items.sort(key=lambda item: item["sort_score"], reverse=True)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    start = (page - 1) * page_size
    items = all_items[start : start + page_size]
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": len(all_items),
        "has_more": start + page_size < len(all_items),
        "suggestions": [] if all_items else ["北门", "小橘", "猫粮", "体育馆"],
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


def navigation(
    db: Session,
    *,
    point_id: UUID,
    from_lng: float | None = None,
    from_lat: float | None = None,
) -> dict:
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
        "route": build_walking_route(
            from_lng=from_lng,
            from_lat=from_lat,
            to_lng=lng,
            to_lat=lat,
        ),
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
                "lng": as_float(point.lng),
                "lat": as_float(point.lat),
            }
            for point in points
        ],
    }


def get_admin_point(db: Session, point_id: UUID) -> MapPoint:
    point = db.scalar(
        select(MapPoint)
        .options(selectinload(MapPoint.area), selectinload(MapPoint.photos))
        .where(MapPoint.id == point_id, MapPoint.deleted_at.is_(None))
    )
    if point is None:
        raise APIError(
            code=ErrorCode.MAP_POINT_NOT_FOUND,
            message="点位不存在",
            status_code=404,
        )
    return point


def admin_point_payload(point: MapPoint) -> dict:
    return {
        "point_id": point.id,
        "campus_id": point.campus_id,
        "area_id": point.area_id,
        "point_type": point.point_type,
        "point_scope": point.point_scope,
        "name": point.name,
        "subtitle": point.subtitle,
        "description": point.description,
        "location_name": point.location_name,
        "location_detail": point.location_detail,
        "lng": as_float(point.lng),
        "lat": as_float(point.lat),
        "amap_poi_id": point.amap_poi_id,
        "amap_address": point.amap_address,
        "route_instruction": point.route_instruction,
        "landmark_hint": point.landmark_hint,
        "entrance_hint": point.entrance_hint,
        "icon_key": point.icon_key,
        "display_level": point.display_level,
        "label_min_zoom": point.label_min_zoom,
        "preview_enabled": point.preview_enabled,
        "preview_min_zoom": point.preview_min_zoom,
        "visibility": point.visibility,
        "status": point.status,
        "cover_photo_url": point_cover_photo(point),
        "photos": [
            photo_payload(photo)
            for photo in sorted(point.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None
        ],
        "updated_at": point.updated_at,
    }


ADMIN_POINT_EDITABLE_FIELDS = {
    "area_id",
    "point_type",
    "point_scope",
    "name",
    "subtitle",
    "description",
    "location_name",
    "location_detail",
    "amap_poi_id",
    "amap_address",
    "route_instruction",
    "landmark_hint",
    "entrance_hint",
    "icon_key",
    "display_level",
    "label_min_zoom",
    "preview_enabled",
    "preview_min_zoom",
    "visibility",
    "status",
}


def admin_point_detail(db: Session, *, point_id: UUID) -> dict:
    return admin_point_payload(get_admin_point(db, point_id))


def update_admin_point(
    db: Session,
    *,
    point_id: UUID,
    admin: User,
    payload: dict,
) -> dict:
    point = get_admin_point(db, point_id)
    for field, value in payload.items():
        if field in ADMIN_POINT_EDITABLE_FIELDS:
            setattr(point, field, value)
    point.updated_by = admin.id
    db.add(point)
    db.commit()
    db.refresh(point)
    return admin_point_payload(point)


def update_admin_point_location(
    db: Session,
    *,
    point_id: UUID,
    admin: User,
    lng: float,
    lat: float,
) -> dict:
    point = get_admin_point(db, point_id)
    point.lng = Decimal(str(lng))
    point.lat = Decimal(str(lat))
    point.geom = point_wkt(lng, lat)
    point.updated_by = admin.id
    db.add(point)
    db.commit()
    db.refresh(point)
    return admin_point_payload(point)
