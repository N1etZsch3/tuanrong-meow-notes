from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import APIError, ErrorCode
from app.modules.auth.models import AdminOperationLog, User
from app.modules.files.service import resolve_business_image
from app.modules.landmarks.schemas import (
    LandmarkCreateRequest,
    LandmarkPhotoRequest,
    LandmarkUpdateRequest,
)
from app.modules.map.models import CampusArea, MapMarkerConfig, MapPoint, MapPointPhoto
from app.modules.map.service import (
    associated_poi_payload,
    get_default_campus,
    map_point_list_item_payload,
)


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _as_float(value) -> float | None:
    return float(value) if value is not None else None


def _resolve_uploaded_file_urls(
    db: Session,
    photo: LandmarkPhotoRequest,
    *,
    uploaded_by: User,
) -> tuple[UUID | None, str | None, str | None]:
    return resolve_business_image(
        db=db,
        current_user=uploaded_by,
        file_id=photo.file_id,
        file_url=photo.file_url,
        thumbnail_url=photo.thumbnail_url,
        allowed_usage_types={"map_point_cover", "map_point_scene", "map_point_route"},
    )


def _landmark_base_statement():
    return select(MapPoint).options(selectinload(MapPoint.photos)).where(
        MapPoint.point_type == "landmark",
        MapPoint.deleted_at.is_(None),
    )


def list_landmarks(
    db: Session,
    *,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """校园地标分页列表。默认只暴露 public+active 点位。"""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    statement = (
        select(MapPoint)
        .options(selectinload(MapPoint.photos), selectinload(MapPoint.area))
        .where(
            MapPoint.point_type == "landmark",
            MapPoint.deleted_at.is_(None),
            MapPoint.visibility == "public",
            MapPoint.status == "active",
        )
    )
    normalized_keyword = keyword.strip() if keyword else ""
    if normalized_keyword:
        like = f"%{normalized_keyword}%"
        statement = statement.outerjoin(CampusArea, MapPoint.area_id == CampusArea.id).where(
            or_(
                MapPoint.name.ilike(like),
                MapPoint.subtitle.ilike(like),
                MapPoint.location_name.ilike(like),
                MapPoint.location_detail.ilike(like),
                CampusArea.name.ilike(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    start = (page - 1) * page_size
    points = db.scalars(
        statement.order_by(MapPoint.created_at.desc(), MapPoint.id.desc())
        .offset(start)
        .limit(page_size)
    ).all()
    return {
        "items": [
            map_point_list_item_payload(point, detail_id=point.id) for point in points
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": start + page_size < total,
    }


def _landmark_icon_key(db: Session) -> str | None:
    return db.scalar(
        select(MapMarkerConfig.marker_key)
        .where(MapMarkerConfig.point_type == "landmark")
        .order_by(MapMarkerConfig.sort_order.asc(), MapMarkerConfig.created_at.asc())
        .limit(1)
    )


def _photo_payload(photo: MapPointPhoto) -> dict:
    return {
        "photo_id": photo.id,
        "photo_type": photo.photo_type,
        "file_url": photo.file_url,
        "thumbnail_url": photo.thumbnail_url,
        "caption": photo.caption,
        "sort_order": photo.sort_order,
        "created_at": photo.created_at,
    }


def _map_point_payload(point: MapPoint) -> dict:
    return {
        "map_point_id": point.id,
        "campus_id": point.campus_id,
        "area_id": point.area_id,
        "point_type": point.point_type,
        "point_scope": point.point_scope,
        "name": point.name,
        "lng": _as_float(point.lng),
        "lat": _as_float(point.lat),
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
        "tencent_poi_lng": _as_float(point.tencent_poi_lng),
        "tencent_poi_lat": _as_float(point.tencent_poi_lat),
        "tencent_poi_distance_meters": point.tencent_poi_distance_meters,
        "tencent_poi_match_method": point.tencent_poi_match_method,
        "associated_poi": associated_poi_payload(point),
    }


def _landmark_detail_payload(point: MapPoint) -> dict:
    return {
        "landmark_id": point.id,
        "map_point_id": point.id,
        "name": point.name,
        "description": point.description,
        "status": point.status,
        "is_public": point.visibility == "public",
        "map_point": _map_point_payload(point),
        "photos": [
            _photo_payload(photo)
            for photo in sorted(point.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None
        ],
        "created_at": point.created_at,
        "updated_at": point.updated_at,
    }


def get_landmark_or_raise(
    db: Session,
    landmark_id: UUID,
    *,
    include_private: bool = False,
) -> MapPoint:
    statement = _landmark_base_statement().where(MapPoint.id == landmark_id)
    if not include_private:
        statement = statement.where(MapPoint.visibility == "public", MapPoint.status == "active")
    point = db.scalar(statement)
    if point is None:
        raise APIError(
            code=ErrorCode.MAP_POINT_NOT_FOUND,
            message="地标不存在",
            status_code=404,
        )
    return point


def _add_photos(
    db: Session,
    *,
    point: MapPoint,
    photos: list[LandmarkPhotoRequest],
    uploaded_by: User,
) -> list[MapPointPhoto]:
    created = []
    cover_exists = any(photo.is_cover for photo in photos)
    for index, photo in enumerate(photos):
        _, file_url, thumbnail_url = _resolve_uploaded_file_urls(
            db,
            photo,
            uploaded_by=uploaded_by,
        )
        if not file_url:
            raise APIError(
                code=ErrorCode.MAP_PARAM_ERROR,
                message="地标照片无效",
                status_code=400,
            )
        is_cover = photo.is_cover or (index == 0 and not cover_exists)
        map_photo = MapPointPhoto(
            map_point_id=point.id,
            file_url=file_url,
            thumbnail_url=thumbnail_url,
            photo_type="cover" if is_cover else photo.photo_type,
            caption=photo.caption,
            sort_order=photo.sort_order if photo.sort_order is not None else index,
            uploaded_by=uploaded_by.id,
        )
        db.add(map_photo)
        db.flush()
        if is_cover:
            point.cover_photo_id = map_photo.id
        created.append(map_photo)
    return created


def create_landmark(
    db: Session,
    *,
    admin: User,
    payload: LandmarkCreateRequest,
) -> dict:
    campus = get_default_campus(db, payload.map_point.campus_id)
    route_instruction = payload.map_point.route_instruction or payload.description
    point = MapPoint(
        campus_id=campus.id,
        area_id=payload.map_point.area_id,
        point_type="landmark",
        point_scope="long_term",
        name=payload.name,
        subtitle="校园地标",
        description=payload.description,
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
        route_instruction=route_instruction,
        landmark_hint=payload.map_point.landmark_hint,
        entrance_hint=payload.map_point.entrance_hint,
        icon_key=_landmark_icon_key(db),
        display_level=50,
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
    photos = _add_photos(db, point=point, photos=payload.photos, uploaded_by=admin)
    db.add(
        AdminOperationLog(
            admin_id=admin.id,
            operation_type="publish",
            target_type="landmark",
            target_id=point.id,
            summary=f"Publish landmark: {point.name}",
            before_data=None,
            after_data={"landmark_id": str(point.id), "map_point_id": str(point.id)},
        )
    )
    db.commit()
    return {
        "landmark_id": point.id,
        "map_point_id": point.id,
        "status": point.status,
        "photo_count": len(photos),
        "created_at": point.created_at,
    }


def _apply_map_point_update(point: MapPoint, payload: LandmarkUpdateRequest) -> None:
    if payload.name is not None:
        point.name = payload.name
        if not point.location_name:
            point.location_name = payload.name
    if payload.description is not None:
        point.description = payload.description
        point.route_instruction = payload.description
    if payload.is_public is not None:
        point.visibility = "public" if payload.is_public else "admin_only"
    if payload.map_point is None:
        return

    values = payload.map_point.model_dump(exclude_unset=True)
    if "lng" in values or "lat" in values:
        lng = values.get("lng", _as_float(point.lng))
        lat = values.get("lat", _as_float(point.lat))
        if lng is None or lat is None:
            raise APIError(
                code=ErrorCode.MAP_PARAM_ERROR,
                message="地标坐标无效",
                status_code=400,
            )
        point.lng = Decimal(str(lng))
        point.lat = Decimal(str(lat))
        point.geom = f"POINT({lng} {lat})"
    for field, value in values.items():
        if field in {"lng", "lat"}:
            continue
        if field in {"tencent_poi_lng", "tencent_poi_lat"} and value is not None:
            setattr(point, field, Decimal(str(value)))
            continue
        setattr(point, field, value)


def update_landmark(
    db: Session,
    *,
    landmark_id: UUID,
    admin: User,
    payload: LandmarkUpdateRequest,
) -> dict:
    point = get_landmark_or_raise(db, landmark_id, include_private=True)
    now = _now()
    before = {"landmark_id": str(point.id), "name": point.name}
    _apply_map_point_update(point, payload)
    point.updated_by = admin.id
    point.updated_at = now
    if payload.photos is not None:
        for photo in point.photos:
            photo.deleted_at = now
        _add_photos(db, point=point, photos=payload.photos, uploaded_by=admin)
    db.add(
        AdminOperationLog(
            admin_id=admin.id,
            operation_type="update",
            target_type="landmark",
            target_id=point.id,
            summary=f"Update landmark: {point.name}",
            before_data=before,
            after_data={"landmark_id": str(point.id), "updated_at": now.isoformat()},
        )
    )
    db.commit()
    return _landmark_detail_payload(get_landmark_or_raise(db, point.id, include_private=True))


def soft_delete_landmark(db: Session, *, landmark_id: UUID, admin: User) -> dict:
    point = get_landmark_or_raise(db, landmark_id, include_private=True)
    now = _now()
    point.deleted_at = now
    point.updated_at = now
    point.updated_by = admin.id
    point.status = "deleted"
    point.visibility = "hidden"
    db.add(
        AdminOperationLog(
            admin_id=admin.id,
            operation_type="delete",
            target_type="landmark",
            target_id=point.id,
            summary=f"Delete landmark: {point.name}",
            before_data={"landmark_id": str(point.id)},
            after_data={"deleted_at": now.isoformat()},
        )
    )
    db.commit()
    return {"landmark_id": point.id, "deleted_at": point.deleted_at}


def get_landmark_detail(
    db: Session,
    *,
    landmark_id: UUID,
    include_private: bool = False,
) -> dict:
    return _landmark_detail_payload(
        get_landmark_or_raise(db, landmark_id, include_private=include_private)
    )
