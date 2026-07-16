import hashlib
import json
from datetime import UTC, date, datetime
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
from app.modules.supplies.models import SupplyPoint, SupplyPointRecord
from app.modules.tasks.execution_state import (
    active_execution as select_active_execution,
)
from app.modules.tasks.execution_state import (
    active_execution_dates as sorted_active_execution_dates,
)
from app.modules.tasks.execution_state import (
    execution_display_status,
    execution_display_status_label,
    local_today,
    normalize_task_lifecycle,
)
from app.modules.tasks.models import Task, TaskPhoto

EARTH_RADIUS_METERS = 6_371_000
AMAP_REST_BASE_URL = "https://restapi.amap.com"
TENCENT_MAP_REST_BASE_URL = "https://apis.map.qq.com"
HBNU_CAMPUS_SEARCH_BOUNDS = {
    "south_west": {"lng": 115.0558, "lat": 30.2248},
    "north_east": {"lng": 115.0693, "lat": 30.2342},
}
HBNU_CAMPUS_POI_KEYWORD = "\u6e56\u5317\u5e08\u8303\u5927\u5b66"
HBNU_CAMPUS_BOUNDS_PADDING_RATIO = 0.35
ALL_MARKER_FILTER_OPTION = {
    "key": "all",
    "label": "全部标记",
    "description": "展示所有已发布地图点位",
    "icon_key": "all",
    "point_types": [],
    "business_types": [],
}
POINT_TYPE_FILTER_META = {
    "task": {
        "label": "任务点",
        "description": "已发布的任务点位",
        "icon_key": "daily_task",
    },
    "cat": {
        "label": "猫咪点",
        "description": "常驻猫咪和高频出现点",
        "icon_key": "cat",
    },
    "supply": {
        "label": "物资点",
        "description": "猫粮、航空箱、诱捕笼等物资点",
        "icon_key": "supply",
    },
    "landmark": {
        "label": "地标",
        "description": "校门、教学楼、食堂等位置",
        "icon_key": "landmark",
    },
}
POINT_TYPE_FILTER_ORDER = ("task", "cat", "supply", "landmark")
MAP_VISIBLE_TASK_STATUSES = {"in_progress", "completed"}
TASK_STATUS_LABELS = {
    "in_progress": "进行中",
    "completed": "已完成",
    "cancelled": "已取消",
    "archived": "已归档",
}


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


def expand_lng_lat_bounds(bounds: dict, padding_ratio: float) -> dict:
    south_west = bounds["south_west"]
    north_east = bounds["north_east"]
    lng_span = north_east["lng"] - south_west["lng"]
    lat_span = north_east["lat"] - south_west["lat"]
    safe_ratio = max(padding_ratio, 0)
    return {
        "south_west": {
            "lng": round(south_west["lng"] - lng_span * safe_ratio, 7),
            "lat": round(south_west["lat"] - lat_span * safe_ratio, 7),
        },
        "north_east": {
            "lng": round(north_east["lng"] + lng_span * safe_ratio, 7),
            "lat": round(north_east["lat"] + lat_span * safe_ratio, 7),
        },
    }


HBNU_CAMPUS_LIMIT_BOUNDS = expand_lng_lat_bounds(
    HBNU_CAMPUS_SEARCH_BOUNDS,
    HBNU_CAMPUS_BOUNDS_PADDING_RATIO,
)


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


def _request_tencent_json(path: str, params: dict) -> dict:
    settings = get_settings()
    key = settings.tencent_map_key.strip()
    if not key:
        return {}
    query = {**params, "key": key}
    secret_key = settings.tencent_map_secret_key.strip()
    if secret_key:
        query["sig"] = tencent_webservice_signature(path, query, secret_key)
    url = f"{TENCENT_MAP_REST_BASE_URL}{path}?{urlencode(query)}"
    with urlopen(url, timeout=settings.tencent_map_service_timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def tencent_webservice_signature(path: str, params: dict, secret_key: str) -> str:
    query = "&".join(f"{key}={params[key]}" for key in sorted(params))
    return hashlib.md5(f"{path}?{query}{secret_key}".encode()).hexdigest()


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


def parse_tencent_polyline(polyline) -> list[dict]:
    if not polyline:
        return []
    if isinstance(polyline, list) and polyline and isinstance(polyline[0], dict):
        points = []
        for item in polyline:
            lng = item.get("lng")
            lat = item.get("lat")
            if lng is None or lat is None:
                continue
            points.append({"lng": float(lng), "lat": float(lat)})
        return points
    if not isinstance(polyline, list) or len(polyline) < 2:
        return []
    values = [float(value) for value in polyline]
    if abs(values[0]) > 90 or abs(values[1]) > 180:
        values[0] = values[0] / 1_000_000
        values[1] = values[1] / 1_000_000
    for index in range(2, len(values)):
        values[index] = values[index - 2] + values[index] / 1_000_000
    points = []
    for index in range(0, len(values) - 1, 2):
        lat = round(values[index], 7)
        lng = round(values[index + 1], 7)
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
        payload = _request_tencent_json(
            "/ws/direction/v1/walking/",
            {
                "from": f"{format_coord(from_lat)},{format_coord(from_lng)}",
                "to": f"{format_coord(to_lat)},{format_coord(to_lng)}",
                "output": "json",
            },
        )
    except Exception:
        return fallback_route(from_lng=from_lng, from_lat=from_lat, to_lng=to_lng, to_lat=to_lat)

    if payload.get("status") != 0:
        return fallback_route(from_lng=from_lng, from_lat=from_lat, to_lng=to_lng, to_lat=to_lat)
    routes = (payload.get("result") or {}).get("routes") or []
    if not routes:
        return fallback_route(from_lng=from_lng, from_lat=from_lat, to_lng=to_lng, to_lat=to_lat)

    route = routes[0]
    route_points = parse_tencent_polyline(route.get("polyline"))
    if not route_points:
        route_points = [
            {"lng": from_lng, "lat": from_lat},
            {"lng": to_lng, "lat": to_lat},
        ]
    steps = []
    for step in route.get("steps") or []:
        polyline_points = parse_tencent_polyline(step.get("polyline"))
        if not polyline_points and step.get("polyline_idx"):
            start, end = step.get("polyline_idx")[:2]
            polyline_points = route_points[start : end + 1]
        steps.append(
            {
                "instruction": step.get("instruction") or "",
                "distance_meters": int(float(step.get("distance") or 0)),
                "duration_seconds": int(float(step.get("duration") or 0) * 60),
                "points": polyline_points,
            }
        )

    return {
        "provider": "tencent",
        "fallback": False,
        "distance_meters": int(float(route.get("distance") or 0)),
        "duration_seconds": int(float(route.get("duration") or 0) * 60),
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
        "core_bounds": HBNU_CAMPUS_SEARCH_BOUNDS,
        "limit_bounds": HBNU_CAMPUS_LIMIT_BOUNDS,
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


def photo_display_urls(photo: MapPointPhoto | TaskPhoto) -> tuple[str, str | None]:
    asset = getattr(photo, "file_asset", None)
    if asset is not None and asset.deleted_at is None:
        return (
            asset.default_url or photo.file_url,
            asset.default_thumb_url or photo.thumbnail_url,
        )
    return photo.file_url, photo.thumbnail_url


def task_cover_photo(task: Task | None) -> str | None:
    if task is None:
        return None
    photos = [photo for photo in task.photos if photo.deleted_at is None]
    cover = next((photo for photo in photos if photo.is_cover), None)
    if cover:
        file_url, thumbnail_url = photo_display_urls(cover)
        return thumbnail_url or file_url
    first_photo = min(photos, key=lambda photo: photo.sort_order, default=None)
    if first_photo is None:
        return None
    file_url, thumbnail_url = photo_display_urls(first_photo)
    return thumbnail_url or file_url


def associated_poi_payload(point: MapPoint) -> dict | None:
    if not point.tencent_poi_id and not point.tencent_poi_name:
        return None
    lng = as_float(point.tencent_poi_lng)
    lat = as_float(point.tencent_poi_lat)
    return {
        "provider": "tencent",
        "poi_id": point.tencent_poi_id,
        "name": point.tencent_poi_name,
        "address": point.tencent_poi_address,
        "category": point.tencent_poi_category,
        "lng": lng,
        "lat": lat,
        "distance_meters": point.tencent_poi_distance_meters,
        "match_method": point.tencent_poi_match_method,
    }


def map_point_cover_photo_url(point: MapPoint) -> str | None:
    """点位封面缩略图 URL：优先 cover_photo_id，否则取 sort_order 最小的照片。"""
    photos = [photo for photo in point.photos if photo.deleted_at is None]
    cover = next((photo for photo in photos if photo.id == point.cover_photo_id), None)
    if cover:
        return cover.thumbnail_url or cover.file_url
    first_photo = min(photos, key=lambda item: item.sort_order, default=None)
    return (first_photo.thumbnail_url or first_photo.file_url) if first_photo else None


def map_point_nearby_landmark_name(point: MapPoint) -> str:
    """列表卡片的"附近地标"文案，语义与前端 getMarkerNearbyLandmarkName 一致。"""
    poi = associated_poi_payload(point)
    if poi:
        name = (poi.get("name") or "").strip() if isinstance(poi.get("name"), str) else ""
        if name:
            return name
        address = (
            (poi.get("address") or "").strip() if isinstance(poi.get("address"), str) else ""
        )
        if address:
            return address
    if point.location_detail and point.location_detail.strip():
        return point.location_detail.strip()
    area_name = point.area.name if point.area else None
    return area_name or point.subtitle or "暂无附近地标"


def map_point_list_item_payload(point: MapPoint, *, detail_id) -> dict:
    """物资/地标列表项，字段形态与前端 MeowPointListItem 对齐。"""
    return {
        "point_id": str(point.id),
        "detail_id": str(detail_id),
        "title": point.name or point.subtitle or "未命名点位",
        "nearby_landmark_name": map_point_nearby_landmark_name(point),
        "cover_photo_url": map_point_cover_photo_url(point),
        "subtitle": point.subtitle,
        "area_name": point.area.name if point.area else None,
    }


def tencent_bounds_boundary() -> str:
    south_west = HBNU_CAMPUS_SEARCH_BOUNDS["south_west"]
    north_east = HBNU_CAMPUS_SEARCH_BOUNDS["north_east"]
    return (
        "rectangle("
        f"{south_west['lat']},{south_west['lng']},"
        f"{north_east['lat']},{north_east['lng']}"
        ")"
    )


def is_inside_campus_bounds(*, lng: float, lat: float) -> bool:
    south_west = HBNU_CAMPUS_SEARCH_BOUNDS["south_west"]
    north_east = HBNU_CAMPUS_SEARCH_BOUNDS["north_east"]
    return (
        south_west["lng"] <= lng <= north_east["lng"]
        and south_west["lat"] <= lat <= north_east["lat"]
    )


def tencent_poi_payload(
    raw: dict,
    *,
    keyword: str,
    anchor_lng: float | None = None,
    anchor_lat: float | None = None,
    match_method: str,
) -> dict | None:
    location = raw.get("location") or {}
    try:
        lng = float(location.get("lng"))
        lat = float(location.get("lat"))
    except (TypeError, ValueError):
        return None
    if not is_inside_campus_bounds(lng=lng, lat=lat):
        return None
    poi_id = raw.get("id") or raw.get("uid") or f"{keyword}-{format_coord(lng)}-{format_coord(lat)}"
    distance = raw.get("_distance")
    if distance is None:
        distance = raw.get("distance")
    try:
        distance_value = int(float(distance)) if distance is not None else None
    except (TypeError, ValueError):
        distance_value = None
    if distance_value is None:
        distance_value = distance_meters(
            from_lng=anchor_lng,
            from_lat=anchor_lat,
            to_lng=lng,
            to_lat=lat,
        )
    return {
        "provider": "tencent",
        "poi_id": str(poi_id),
        "name": raw.get("title") or raw.get("name") or keyword,
        "address": raw.get("address") or None,
        "category": raw.get("category") or raw.get("type") or None,
        "lng": lng,
        "lat": lat,
        "distance_meters": distance_value,
        "match_method": match_method,
    }


def search_tencent_pois(
    *,
    keyword: str,
    boundary: str,
    anchor_lng: float | None = None,
    anchor_lat: float | None = None,
    limit: int = 20,
    match_method: str = "search",
) -> list[dict]:
    try:
        payload = _request_tencent_json(
            "/ws/place/v1/search",
            {
                "keyword": keyword,
                "boundary": boundary,
                "orderby": "_distance",
                "page_size": str(min(max(limit, 1), 20)),
                "page_index": "1",
                "output": "json",
            },
        )
    except Exception:
        return []
    if payload.get("status") != 0:
        return []
    pois = []
    for raw in payload.get("data") or []:
        poi = tencent_poi_payload(
            raw,
            keyword=keyword,
            anchor_lng=anchor_lng,
            anchor_lat=anchor_lat,
            match_method=match_method,
        )
        if poi:
            pois.append(poi)
    pois.sort(
        key=lambda item: (
            item["distance_meters"] if item["distance_meters"] is not None else 999_999,
            item["name"],
        )
    )
    return pois


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
        .options(
            selectinload(Task.execution_dates),
            selectinload(Task.photos).selectinload(TaskPhoto.file_asset),
            selectinload(Task.map_point),
        )
        .where(
            Task.map_point_id.in_(point_ids),
            Task.deleted_at.is_(None),
        )
    ).all()
    changed = False
    now = datetime.now(tz=UTC)
    today = local_today(now)
    for task in tasks:
        changed = normalize_task_lifecycle(task, today=today, now=now) or changed
    if changed:
        db.commit()
        tasks = db.scalars(
            select(Task)
            .options(
                selectinload(Task.execution_dates),
                selectinload(Task.photos).selectinload(TaskPhoto.file_asset),
            )
            .where(
                Task.map_point_id.in_(point_ids),
                Task.deleted_at.is_(None),
            )
        ).all()
    return {task.map_point_id: task for task in tasks}


def supply_by_map_point_ids(db: Session, points: list[MapPoint]) -> dict[UUID, SupplyPoint]:
    point_ids = [point.id for point in points if point.point_type == "supply"]
    if not point_ids:
        return {}
    supplies = db.scalars(
        select(SupplyPoint)
        .options(
            selectinload(SupplyPoint.map_point).selectinload(MapPoint.photos),
            selectinload(SupplyPoint.items),
            selectinload(SupplyPoint.records)
            .selectinload(SupplyPointRecord.recorder)
            .selectinload(User.profile),
            selectinload(SupplyPoint.records).selectinload(SupplyPointRecord.items),
        )
        .where(
            SupplyPoint.map_point_id.in_(point_ids),
            SupplyPoint.deleted_at.is_(None),
            SupplyPoint.status == "active",
        )
    ).all()
    return {supply.map_point_id: supply for supply in supplies}


def filter_points_with_visible_task_business(
    points: list[MapPoint],
    task_lookup: dict[UUID, Task],
) -> list[MapPoint]:
    return [
        point
        for point in points
        if point.point_type != "task"
        or task_lookup.get(point.id) is None
        or task_lookup[point.id].status in MAP_VISIBLE_TASK_STATUSES
    ]


def next_task_execution_date(task: Task) -> str | None:
    today = date.today()
    active_dates = sorted_active_execution_dates(task.execution_dates)
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
    return sorted_active_execution_dates(task.execution_dates)


def active_task_execution_payload(task: Task | None) -> dict | None:
    if task is None or task.task_type != "feeding":
        return None
    today = date.today()
    execution = select_active_execution(task.execution_dates, today=today)
    if execution is None:
        return None
    display_status = execution_display_status(execution, today=today)
    return {
        "execution_date_id": execution.id,
        "execute_date": execution.execute_date.isoformat(),
        "status": execution.status,
        "display_status": display_status,
        "display_status_label": execution_display_status_label(display_status),
        "completed_at": execution.completed_at,
        "checkin_id": execution.checkin_id,
    }


def feeding_task_marker_status(task: Task | None) -> str | None:
    if task is None or task.task_type != "feeding":
        return None
    active_payload = active_task_execution_payload(task)
    if active_payload and active_payload["display_status"] == "completed":
        return "completed"
    return "pending"


def task_status_label(task: Task | None) -> str | None:
    if task is None:
        return None
    return TASK_STATUS_LABELS.get(task.status, task.status)


def task_marker_extra(task: Task | None) -> dict:
    if task is None:
        return {}
    extra = {
        "task_status": task.status,
        "task_status_label": task_status_label(task),
        "next_execute_date": next_task_execution_date(task),
        "today_status": today_task_execution_status(task),
    }
    active_payload = active_task_execution_payload(task)
    if active_payload:
        extra["active_execution"] = active_payload
    feeding_status = feeding_task_marker_status(task)
    if feeding_status:
        extra["feeding_status"] = feeding_status
    return extra


def supply_item_label(item) -> str:
    return f"{item.item_name} x{item.quantity}{item.unit or ''}"


def supply_item_payload(item) -> dict:
    return {
        "item_id": getattr(item, "id", None),
        "source_item_id": getattr(item, "supply_point_item_id", None),
        "item_name": item.item_name,
        "item_type": item.item_type,
        "quantity": item.quantity,
        "unit": item.unit,
        "icon_key": item.icon_key,
        "color_key": item.color_key,
        "is_custom": item.is_custom,
        "sort_order": item.sort_order,
        "label": supply_item_label(item),
    }


def supply_active_items(supply: SupplyPoint) -> list:
    return sorted(
        [item for item in supply.items if item.deleted_at is None],
        key=lambda item: item.sort_order,
    )


def supply_latest_record(supply: SupplyPoint):
    records = sorted(
        [record for record in supply.records if record.deleted_at is None],
        key=lambda record: record.recorded_at or record.created_at,
        reverse=True,
    )
    return records[0] if records else None


def supply_marker_extra(supply: SupplyPoint | None) -> dict:
    if supply is None:
        return {}
    latest = supply_latest_record(supply)
    current_items = (
        [
            supply_item_payload(item)
            for item in sorted(latest.items, key=lambda item: item.sort_order)
        ]
        if latest
        else [supply_item_payload(item) for item in supply_active_items(supply)]
    )
    return {
        "supply_point_id": supply.id,
        "status": supply.status,
        "current_state_source": "latest_record" if latest else "initial",
        "current_items": current_items,
        "latest_record": {
            "record_id": latest.id,
            "recorded_at": latest.recorded_at,
            "match_status": latest.match_status,
            "display_tone": latest.display_tone,
        }
        if latest
        else None,
    }


def supply_cover_photo(supply: SupplyPoint | None) -> str | None:
    if supply is None:
        return None
    photos = [photo for photo in supply.map_point.photos if photo.deleted_at is None]
    cover = next((photo for photo in photos if photo.id == supply.map_point.cover_photo_id), None)
    if cover:
        return cover.thumbnail_url or cover.file_url
    first_photo = min(photos, key=lambda item: item.sort_order, default=None)
    return (first_photo.thumbnail_url or first_photo.file_url) if first_photo else None


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
    supply: SupplyPoint | None = None,
) -> dict:
    lng = as_float(point.lng)
    lat = as_float(point.lat)
    extra = task_marker_extra(task)
    extra.update(supply_marker_extra(supply))
    associated_poi = associated_poi_payload(point)
    if associated_poi:
        extra["associated_poi"] = associated_poi
    if point.location_name:
        extra["location_name"] = point.location_name
    if point.location_detail:
        extra["location_detail"] = point.location_detail
    return {
        "point_id": point.id,
        "point_type": point.point_type,
        "point_scope": point.point_scope,
        "business_type": point_business_type(point, configs),
        "business_id": task.id if task else (supply.id if supply else point.id),
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
        "cover_photo_url": (
            task_cover_photo(task) or supply_cover_photo(supply) or point_cover_photo(point)
        ),
        "preview_enabled": point.preview_enabled,
        "preview_min_zoom": point.preview_min_zoom,
        "label_min_zoom": point.label_min_zoom,
        "distance_meters": distance_meters(
            from_lng=user_lng,
            from_lat=user_lat,
            to_lng=lng,
            to_lat=lat,
        ),
        "extra": extra,
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
        "tencent_config": {
            "map_provider": "tencent",
            "referer": settings.tencent_map_referer,
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
    points = filter_points_with_visible_task_business(points, task_lookup)
    point_types = {
        point.point_type
        for point in points
        if not (
            point.point_type == "task"
            and point_business_type(point, configs) == "feeding"
        )
    }
    marker_options = [
        point_type_filter_option(point_type)
        for point_type in sorted(
            point_types,
            key=lambda value: (
                POINT_TYPE_FILTER_ORDER.index(value)
                if value in POINT_TYPE_FILTER_ORDER
                else len(POINT_TYPE_FILTER_ORDER),
                value,
            ),
        )
    ]
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
    published_options = [*marker_options, *options[1:]]
    options = [options[0]]
    if len(published_options) >= 2:
        options.append(all_marker_filter_option(published_options))
    options.extend(published_options)
    return options


def all_marker_filter_option(marker_options: list[dict]) -> dict:
    option = dict(ALL_MARKER_FILTER_OPTION)
    point_types = {
        point_type
        for marker_option in marker_options
        for point_type in marker_option.get("point_types", [])
    }
    if point_types == {"task"}:
        option["label"] = "全部任务类型"
        option["description"] = "展示所有任务类型"
    return option


def point_type_filter_option(point_type: str) -> dict:
    meta = POINT_TYPE_FILTER_META.get(point_type, {})
    return {
        "key": point_type,
        "label": meta.get("label", point_type),
        "description": meta.get("description", ""),
        "icon_key": meta.get("icon_key", point_type),
        "point_types": [point_type],
        "business_types": [],
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
    campus_limit_south_west = HBNU_CAMPUS_LIMIT_BOUNDS["south_west"]
    campus_limit_north_east = HBNU_CAMPUS_LIMIT_BOUNDS["north_east"]
    effective_min_lng = max(
        min_lng if min_lng is not None else campus_limit_south_west["lng"],
        campus_limit_south_west["lng"],
    )
    effective_max_lng = min(
        max_lng if max_lng is not None else campus_limit_north_east["lng"],
        campus_limit_north_east["lng"],
    )
    effective_min_lat = max(
        min_lat if min_lat is not None else campus_limit_south_west["lat"],
        campus_limit_south_west["lat"],
    )
    effective_max_lat = min(
        max_lat if max_lat is not None else campus_limit_north_east["lat"],
        campus_limit_north_east["lat"],
    )
    statement = statement.where(
        MapPoint.lng >= effective_min_lng,
        MapPoint.lng <= effective_max_lng,
        MapPoint.lat >= effective_min_lat,
        MapPoint.lat <= effective_max_lat,
    )

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
    supply_lookup = supply_by_map_point_ids(db, points)
    points = filter_points_with_visible_task_business(points, task_lookup)
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
                supply=supply_lookup.get(point.id),
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
        point.tencent_poi_name,
        point.tencent_poi_address,
        point.tencent_poi_category,
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
    pois = search_tencent_pois(
        keyword=keyword,
        boundary=tencent_bounds_boundary(),
        anchor_lng=user_lng if user_lng is not None else as_float(campus.center_lng),
        anchor_lat=user_lat if user_lat is not None else as_float(campus.center_lat),
        limit=limit,
        match_method="search",
    )
    results = []
    for index, poi in enumerate(pois):
        results.append(
            {
                "result_type": "external_poi",
                "map_point_id": None,
                "business_id": f"tencent:{poi['poi_id']}",
                "point_type": "landmark",
                "business_type": "tencent_poi",
                "title": poi["name"],
                "subtitle": poi["category"] or "腾讯地图点位",
                "description": poi["address"],
                "icon_key": "landmark",
                "cover_photo_url": None,
                "lng": poi["lng"],
                "lat": poi["lat"],
                "distance_meters": poi["distance_meters"],
                "status_label": "地图点位",
                "highlight_text": keyword,
                "sort_score": 50 - index,
                "poi": poi,
            }
        )
    return results


def resolve_poi(
    *,
    keyword: str,
    lng: float,
    lat: float,
    radius: int = 120,
    limit: int = 5,
) -> dict:
    normalized_keyword = keyword.strip() or "湖北师范大学"
    boundary = f"nearby({format_coord(lat)},{format_coord(lng)},{max(min(radius, 1000), 10)})"
    candidates = search_tencent_pois(
        keyword=normalized_keyword,
        boundary=boundary,
        anchor_lng=lng,
        anchor_lat=lat,
        limit=limit,
        match_method="poi_tap",
    )
    matched = candidates[0] if candidates else {
        "provider": "tencent",
        "poi_id": None,
        "name": normalized_keyword,
        "address": None,
        "category": None,
        "lng": lng,
        "lat": lat,
        "distance_meters": 0,
        "match_method": "poi_tap_fallback",
    }
    return {
        "query": {
            "keyword": normalized_keyword,
            "lng": lng,
            "lat": lat,
            "radius": radius,
        },
        "matched_poi": matched,
        "candidates": candidates,
    }


def nearby_pois(
    *,
    lng: float,
    lat: float,
    keyword: str | None = None,
    radius: int = 180,
    limit: int = 8,
) -> dict:
    normalized_keyword = (keyword or HBNU_CAMPUS_POI_KEYWORD).strip() or HBNU_CAMPUS_POI_KEYWORD
    boundary = f"nearby({format_coord(lat)},{format_coord(lng)},{max(min(radius, 1000), 10)})"
    candidates = search_tencent_pois(
        keyword=normalized_keyword,
        boundary=boundary,
        anchor_lng=lng,
        anchor_lat=lat,
        limit=limit,
        match_method="nearby",
    )
    fallback_keyword = None
    if not candidates and normalized_keyword != HBNU_CAMPUS_POI_KEYWORD:
        fallback_keyword = HBNU_CAMPUS_POI_KEYWORD
        candidates = search_tencent_pois(
            keyword=fallback_keyword,
            boundary=boundary,
            anchor_lng=lng,
            anchor_lat=lat,
            limit=limit,
            match_method="nearby_fallback",
        )
    query = {
        "keyword": normalized_keyword,
        "lng": lng,
        "lat": lat,
        "radius": radius,
    }
    if fallback_keyword:
        query["fallback_keyword"] = fallback_keyword
    return {
        "query": query,
        "recommended": candidates[0] if candidates else None,
        "candidates": candidates,
    }


def walking_route_between(
    *,
    from_lng: float,
    from_lat: float,
    to_lng: float,
    to_lat: float,
) -> dict:
    return build_walking_route(
        from_lng=from_lng,
        from_lat=from_lat,
        to_lng=to_lng,
        to_lat=to_lat,
    )


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
            "description": item["extra"].get("location_detail")
            or points_by_id[item["point_id"]].description,
            "icon_key": item["icon_key"],
            "cover_photo_url": item["cover_photo_url"],
            "lng": item["lng"],
            "lat": item["lat"],
            "distance_meters": item["distance_meters"],
            "status_label": item["extra"].get("task_status_label")
            or point_label_for_type(item["point_type"], item["business_type"]),
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


def photo_payload(photo: MapPointPhoto | TaskPhoto) -> dict:
    file_url, thumbnail_url = photo_display_urls(photo)
    return {
        "photo_id": photo.id,
        "photo_type": photo.photo_type,
        "file_url": file_url,
        "thumbnail_url": thumbnail_url,
        "caption": photo.caption,
        "sort_order": photo.sort_order,
        "created_at": photo.created_at,
    }


def summary_photos(point: MapPoint, task: Task | None) -> list[dict]:
    if task is not None:
        task_photos = [
            photo
            for photo in sorted(task.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None
        ]
        if task_photos:
            return [photo_payload(photo) for photo in task_photos]

    return [
        photo_payload(photo)
        for photo in sorted(point.photos, key=lambda item: item.sort_order)
        if photo.deleted_at is None
    ]


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
    supply = supply_by_map_point_ids(db, [point]).get(point.id)
    lng = as_float(point.lng)
    lat = as_float(point.lat)
    business_type = point_business_type(point, configs)
    tags = [point_label(point, configs), point_label_for_type(point.point_type, business_type)]
    business_summary = task_marker_extra(task)
    business_summary.update(supply_marker_extra(supply))
    return {
        "point_id": point.id,
        "point_type": point.point_type,
        "business_type": business_type,
        "business_id": task.id if task else (supply.id if supply else point.id),
        "title": point.name,
        "subtitle": point.subtitle,
        "cover_photo_url": (
            task_cover_photo(task) or supply_cover_photo(supply) or point_cover_photo(point)
        ),
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
        "associated_poi": associated_poi_payload(point),
        "photos": summary_photos(point, task),
        "business_summary": business_summary,
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
                "path": detail_path(point, task, supply),
                "target_type": "page",
            },
        ],
    }


def detail_path(
    point: MapPoint,
    task: Task | None = None,
    supply: SupplyPoint | None = None,
) -> str:
    if point.point_type == "task":
        if task:
            return f"/pages/tasks/detail?task_id={task.id}"
        return f"/pages/tasks/detail?map_point_id={point.id}"
    if point.point_type == "cat":
        return f"/pages/cats/detail?map_point_id={point.id}"
    if point.point_type == "supply":
        if supply:
            return f"/pages/supplies/detail?supply_point_id={supply.id}"
        return f"/pages/supplies/detail?map_point_id={point.id}"
    if point.point_type == "landmark":
        return f"/pages/landmarks/detail?landmark_id={point.id}"
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
    encoded_referer = quote(get_settings().tencent_map_referer)
    return {
        "point_id": point.id,
        "title": point.name,
        "destination": {
            "lng": lng,
            "lat": lat,
            "location_name": title,
            "amap_poi_id": point.amap_poi_id,
            "amap_address": point.amap_address,
            "associated_poi": associated_poi_payload(point),
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
        "tencent_navigation": {
            "mode": "walking",
            "web_url": (
                "https://apis.map.qq.com/uri/v1/routeplan"
                f"?type=walk&to={encoded_title}&tocoord={lat},{lng}&referer={encoded_referer}"
            ),
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
    items = []
    for point in points:
        task = task_lookup.get(point.id)
        active_execution = active_task_execution_payload(task)
        items.append(
            {
                "id": task.id if task else point.id,
                "type": "emergency_task"
                if point_business_type(point, configs) == "emergency"
                else "daily_task",
                "title": task.title if task else point.name,
                "subtitle": point.subtitle,
                "description": point.location_detail
                or (task.description if task else point.description),
                "distance_meters": None,
                "status_label": (
                    active_execution["display_status_label"]
                    if active_execution
                    else task_status_label(task)
                )
                or point_label_for_type(
                    point.point_type,
                    point_business_type(point, configs),
                ),
                "tag_label": point_label(point, configs),
                "cover_photo_url": task_cover_photo(task) or point_cover_photo(point),
                "map_point_id": point.id,
                "lng": as_float(point.lng),
                "lat": as_float(point.lat),
                "active_execution": active_execution,
            }
        )
    return {
        "content_type": "latest_tasks" if mode == "auto" else mode,
        "title": "最新任务",
        "items": items,
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
        "tencent_poi_id": point.tencent_poi_id,
        "tencent_poi_name": point.tencent_poi_name,
        "tencent_poi_address": point.tencent_poi_address,
        "tencent_poi_category": point.tencent_poi_category,
        "tencent_poi_lng": as_float(point.tencent_poi_lng),
        "tencent_poi_lat": as_float(point.tencent_poi_lat),
        "tencent_poi_distance_meters": point.tencent_poi_distance_meters,
        "tencent_poi_match_method": point.tencent_poi_match_method,
        "associated_poi": associated_poi_payload(point),
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
    "tencent_poi_id",
    "tencent_poi_name",
    "tencent_poi_address",
    "tencent_poi_category",
    "tencent_poi_lng",
    "tencent_poi_lat",
    "tencent_poi_distance_meters",
    "tencent_poi_match_method",
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
