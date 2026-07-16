from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import APIError
from app.modules.auth.models import AdminOperationLog, User
from app.modules.files.service import resolve_business_image
from app.modules.map.models import CampusArea, MapPoint, MapPointPhoto
from app.modules.map.service import (
    associated_poi_payload,
    get_default_campus,
    map_point_list_item_payload,
)
from app.modules.supplies.models import (
    SupplyPoint,
    SupplyPointItem,
    SupplyPointRecord,
    SupplyPointRecordItem,
)
from app.modules.supplies.schemas import (
    SupplyPointCreateRequest,
    SupplyPointItemRequest,
    SupplyPointPhotoRequest,
    SupplyPointUpdateRequest,
    SupplyRecordCreateRequest,
    UploadedFileRef,
)

SUPPLY_ERROR_PARAM = 64001
SUPPLY_ERROR_NOT_FOUND = 64004
SUPPLY_ERROR_MAP_POINT_INVALID = 64005
SUPPLY_ERROR_ITEM_INVALID = 64006
SUPPLY_ERROR_PHOTO_INVALID = 64007


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _as_float(value) -> float | None:
    return float(value) if value is not None else None


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _end_of_day(value: date) -> datetime:
    return datetime.combine(value, time.max, tzinfo=UTC)


def _user_payload(user: User | None) -> dict | None:
    if user is None:
        return None
    return {
        "user_id": user.id,
        "nickname": user.profile.nickname if user.profile else user.student_no,
        "avatar_url": user.profile.avatar_url if user.profile else None,
    }


def _supply_base_statement():
    return select(SupplyPoint).options(
        selectinload(SupplyPoint.map_point).selectinload(MapPoint.photos),
        selectinload(SupplyPoint.items),
        selectinload(SupplyPoint.records)
        .selectinload(SupplyPointRecord.recorder)
        .selectinload(User.profile),
        selectinload(SupplyPoint.records).selectinload(SupplyPointRecord.items),
    )


def list_supply_points(
    db: Session,
    *,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """物资点分页列表。detail_id 用 SupplyPoint 业务 id（前端详情页据此打开）。"""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    statement = (
        select(SupplyPoint)
        .join(MapPoint, SupplyPoint.map_point_id == MapPoint.id)
        .options(
            selectinload(SupplyPoint.map_point).selectinload(MapPoint.photos),
            selectinload(SupplyPoint.map_point).selectinload(MapPoint.area),
        )
        .where(
            SupplyPoint.deleted_at.is_(None),
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
    supplies = db.scalars(
        statement.order_by(MapPoint.created_at.desc(), SupplyPoint.id.desc())
        .offset(start)
        .limit(page_size)
    ).all()
    return {
        "items": [
            map_point_list_item_payload(supply.map_point, detail_id=supply.id)
            for supply in supplies
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": start + page_size < total,
    }


def _active_items(supply: SupplyPoint) -> list[SupplyPointItem]:
    return sorted(
        [item for item in supply.items if item.deleted_at is None],
        key=lambda item: item.sort_order,
    )


def _active_records(supply: SupplyPoint) -> list[SupplyPointRecord]:
    return sorted(
        [record for record in supply.records if record.deleted_at is None],
        key=lambda record: record.recorded_at or record.created_at,
        reverse=True,
    )


def _latest_record(supply: SupplyPoint) -> SupplyPointRecord | None:
    records = _active_records(supply)
    return records[0] if records else None


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


def get_supply_or_raise(
    db: Session,
    supply_point_id: UUID,
    *,
    include_private: bool = False,
) -> SupplyPoint:
    statement = _supply_base_statement().where(
        SupplyPoint.id == supply_point_id,
        SupplyPoint.deleted_at.is_(None),
    )
    if not include_private:
        statement = statement.where(
            SupplyPoint.is_public.is_(True),
            SupplyPoint.status == "active",
        )
    supply = db.scalar(statement)
    if supply is None:
        raise APIError(
            code=SUPPLY_ERROR_NOT_FOUND,
            message="Supply point not found",
            status_code=404,
        )
    return supply


def get_supply_by_map_point(db: Session, map_point_id: UUID) -> SupplyPoint | None:
    return db.scalar(
        _supply_base_statement().where(
            SupplyPoint.map_point_id == map_point_id,
            SupplyPoint.deleted_at.is_(None),
            SupplyPoint.status == "active",
        )
    )


def supply_by_map_point_ids(db: Session, points: list[MapPoint]) -> dict[UUID, SupplyPoint]:
    point_ids = [point.id for point in points if point.point_type == "supply"]
    if not point_ids:
        return {}
    supplies = db.scalars(
        _supply_base_statement().where(
            SupplyPoint.map_point_id.in_(point_ids),
            SupplyPoint.deleted_at.is_(None),
            SupplyPoint.status == "active",
        )
    ).all()
    return {supply.map_point_id: supply for supply in supplies}


def _item_payload(item: SupplyPointItem | SupplyPointRecordItem) -> dict:
    item_id = getattr(item, "id", None)
    source_item_id = getattr(item, "supply_point_item_id", None)
    return {
        "item_id": item_id,
        "source_item_id": source_item_id,
        "item_name": item.item_name,
        "item_type": item.item_type,
        "quantity": item.quantity,
        "unit": item.unit,
        "icon_key": item.icon_key,
        "color_key": item.color_key,
        "is_custom": item.is_custom,
        "sort_order": item.sort_order,
        "label": _item_label(item),
    }


def _item_label(item: SupplyPointItem | SupplyPointRecordItem) -> str:
    unit = item.unit or ""
    return f"{item.item_name} x{item.quantity}{unit}"


def _record_payload(record: SupplyPointRecord) -> dict:
    return {
        "record_id": record.id,
        "supply_point_id": record.supply_point_id,
        "recorded_at": record.recorded_at,
        "match_status": record.match_status,
        "display_tone": record.display_tone,
        "recorder": _user_payload(record.recorder),
        "photo": {
            "file_id": record.photo_file_id,
            "file_url": record.photo_file_url,
            "thumbnail_url": record.photo_thumbnail_url,
            "cos_object_key": record.photo_cos_object_key,
        },
        "remark": record.remark,
        "items": [
            _item_payload(item)
            for item in sorted(record.items, key=lambda item: item.sort_order)
        ],
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


def _supply_detail_payload(
    supply: SupplyPoint,
    *,
    record_page: int = 1,
    record_page_size: int = 20,
    record_date: date | None = None,
    record_week_start: date | None = None,
    record_month: str | None = None,
) -> dict:
    records = _filter_records(
        _active_records(supply),
        record_date=record_date,
        record_week_start=record_week_start,
        record_month=record_month,
    )
    latest = _latest_record(supply)
    initial_items = [_item_payload(item) for item in _active_items(supply)]
    current_items = (
        [_item_payload(item) for item in sorted(latest.items, key=lambda item: item.sort_order)]
        if latest
        else initial_items
    )
    start = (record_page - 1) * record_page_size
    end = start + record_page_size
    paged_records = records[start:end]
    return {
        "supply_point_id": supply.id,
        "map_point_id": supply.map_point_id,
        "name": supply.name,
        "description": supply.description,
        "usage_instruction": supply.usage_instruction,
        "access_instruction": supply.access_instruction,
        "status": supply.status,
        "is_public": supply.is_public,
        "map_point": _map_point_payload(supply.map_point),
        "photos": [
            _photo_payload(photo)
            for photo in sorted(supply.map_point.photos, key=lambda item: item.sort_order)
            if photo.deleted_at is None
        ],
        "initial_items": initial_items,
        "current_state_source": "latest_record" if latest else "initial",
        "current_items": current_items,
        "latest_record": _record_payload(latest) if latest else None,
        "records": {
            "items": [_record_payload(record) for record in paged_records],
            "page": record_page,
            "page_size": record_page_size,
            "total": len(records),
            "has_more": end < len(records),
        },
        "created_at": supply.created_at,
        "updated_at": supply.updated_at,
    }


def _filter_records(
    records: list[SupplyPointRecord],
    *,
    record_date: date | None = None,
    record_week_start: date | None = None,
    record_month: str | None = None,
) -> list[SupplyPointRecord]:
    if record_date is None and record_week_start is None and record_month is None:
        return records
    filtered: list[SupplyPointRecord] = []
    week_end = None
    if record_week_start:
        week_end = record_week_start.toordinal() + 6
    for record in records:
        recorded_at = record.recorded_at or record.created_at
        local_date = recorded_at.date()
        if record_date and local_date != record_date:
            continue
        if record_week_start and not (
            record_week_start.toordinal() <= local_date.toordinal() <= week_end
        ):
            continue
        if record_month and not local_date.isoformat().startswith(record_month):
            continue
        filtered.append(record)
    return filtered


def supply_marker_extra(supply: SupplyPoint | None) -> dict:
    if supply is None:
        return {}
    latest = _latest_record(supply)
    current_items = (
        [_item_payload(item) for item in sorted(latest.items, key=lambda item: item.sort_order)]
        if latest
        else [_item_payload(item) for item in _active_items(supply)]
    )
    return {
        "supply_point_id": supply.id,
        "status": supply.status,
        "current_state_source": "latest_record" if latest else "initial",
        "current_items": current_items,
        "latest_record": _record_payload(latest) if latest else None,
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


def _create_map_point(db: Session, *, payload: SupplyPointCreateRequest, admin: User) -> MapPoint:
    if payload.map_point_id is not None:
        point = db.get(MapPoint, payload.map_point_id)
        if point is None or point.deleted_at is not None:
            raise APIError(
                code=SUPPLY_ERROR_MAP_POINT_INVALID,
                message="Map point is invalid",
                status_code=400,
            )
        point.point_type = "supply"
        point.point_scope = "long_term"
        point.name = payload.name
        point.subtitle = "Supply Point"
        point.description = payload.description
        point.icon_key = "supply_food"
        point.visibility = "public" if payload.is_public else "admin_only"
        point.updated_by = admin.id
        return point
    if payload.map_point is None:
        raise APIError(
            code=SUPPLY_ERROR_MAP_POINT_INVALID,
            message="Map point is required",
            status_code=400,
        )
    campus = get_default_campus(db, payload.map_point.campus_id)
    point = MapPoint(
        campus_id=campus.id,
        area_id=payload.map_point.area_id,
        point_type="supply",
        point_scope="long_term",
        name=payload.name,
        subtitle="Supply Point",
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
        route_instruction=payload.map_point.route_instruction,
        landmark_hint=payload.map_point.landmark_hint,
        entrance_hint=payload.map_point.entrance_hint,
        icon_key="supply_food",
        display_level=30,
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


def _apply_map_point_update(point: MapPoint, payload: SupplyPointUpdateRequest) -> None:
    if payload.name is not None:
        point.name = payload.name
    if payload.description is not None:
        point.description = payload.description
    if payload.is_public is not None:
        point.visibility = "public" if payload.is_public else "admin_only"
    if payload.map_point is None:
        return
    point.lng = Decimal(str(payload.map_point.lng))
    point.lat = Decimal(str(payload.map_point.lat))
    point.geom = f"POINT({payload.map_point.lng} {payload.map_point.lat})"
    point.location_name = payload.map_point.location_name
    point.location_detail = payload.map_point.location_detail
    point.route_instruction = payload.map_point.route_instruction
    point.landmark_hint = payload.map_point.landmark_hint
    point.entrance_hint = payload.map_point.entrance_hint
    point.amap_poi_id = payload.map_point.amap_poi_id
    point.amap_address = payload.map_point.amap_address
    point.tencent_poi_id = payload.map_point.tencent_poi_id
    point.tencent_poi_name = payload.map_point.tencent_poi_name
    point.tencent_poi_address = payload.map_point.tencent_poi_address
    point.tencent_poi_category = payload.map_point.tencent_poi_category
    point.tencent_poi_lng = (
        Decimal(str(payload.map_point.tencent_poi_lng))
        if payload.map_point.tencent_poi_lng is not None
        else None
    )
    point.tencent_poi_lat = (
        Decimal(str(payload.map_point.tencent_poi_lat))
        if payload.map_point.tencent_poi_lat is not None
        else None
    )
    point.tencent_poi_distance_meters = payload.map_point.tencent_poi_distance_meters
    point.tencent_poi_match_method = payload.map_point.tencent_poi_match_method


def _replace_items(
    db: Session,
    *,
    supply: SupplyPoint,
    item_payloads: list[SupplyPointItemRequest],
    now: datetime | None = None,
) -> list[SupplyPointItem]:
    now = now or _now()
    for item in _active_items(supply):
        item.deleted_at = now
        item.status = "deleted"
    created = []
    for index, item in enumerate(item_payloads):
        created_item = SupplyPointItem(
            supply_point_id=supply.id,
            item_name=item.item_name,
            item_type=item.item_type or "custom",
            quantity=item.quantity,
            unit=item.unit,
            icon_key=item.icon_key,
            color_key=item.color_key,
            is_custom=item.is_custom,
            sort_order=item.sort_order if item.sort_order is not None else index,
            status="active",
        )
        db.add(created_item)
        created.append(created_item)
    return created


def _add_photos(
    db: Session,
    *,
    point: MapPoint,
    photos: list[SupplyPointPhotoRequest],
    uploaded_by: User,
) -> list[MapPointPhoto]:
    created = []
    cover_exists = any(photo.is_cover for photo in photos)
    for index, photo in enumerate(photos):
        _, file_url, thumbnail_url = _resolve_uploaded_file_urls(
            db,
            photo,
            uploaded_by=uploaded_by,
            allowed_usage_types={"map_point_cover", "map_point_scene", "map_point_route"},
        )
        if not file_url:
            raise APIError(
                code=SUPPLY_ERROR_PHOTO_INVALID,
                message="Supply point photo is invalid",
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


def publish_supply_point(
    db: Session,
    *,
    admin: User,
    payload: SupplyPointCreateRequest,
) -> dict:
    now = _now()
    point = _create_map_point(db, payload=payload, admin=admin)
    supply = SupplyPoint(
        map_point_id=point.id,
        name=payload.name,
        description=payload.description,
        usage_instruction=payload.usage_instruction,
        access_instruction=payload.access_instruction or point.route_instruction,
        status="active",
        is_public=payload.is_public,
        created_by=admin.id,
        updated_by=admin.id,
    )
    db.add(supply)
    db.flush()
    items = _replace_items(db, supply=supply, item_payloads=payload.items, now=now)
    photos = _add_photos(db, point=point, photos=payload.photos, uploaded_by=admin)
    db.add(
        AdminOperationLog(
            admin_id=admin.id,
            operation_type="publish",
            target_type="supply_point",
            target_id=supply.id,
            summary=f"Publish supply point: {supply.name}",
            before_data=None,
            after_data={"supply_point_id": str(supply.id), "map_point_id": str(point.id)},
        )
    )
    db.commit()
    return {
        "supply_point_id": supply.id,
        "map_point_id": point.id,
        "status": supply.status,
        "initial_item_count": len(items),
        "photo_count": len(photos),
        "created_at": supply.created_at,
    }


def update_supply_point(
    db: Session,
    *,
    supply_point_id: UUID,
    admin: User,
    payload: SupplyPointUpdateRequest,
) -> dict:
    supply = get_supply_or_raise(db, supply_point_id, include_private=True)
    now = _now()
    before = {"name": supply.name, "map_point_id": str(supply.map_point_id)}
    if payload.name is not None:
        supply.name = payload.name
    if payload.description is not None:
        supply.description = payload.description
    if payload.usage_instruction is not None:
        supply.usage_instruction = payload.usage_instruction
    if payload.access_instruction is not None:
        supply.access_instruction = payload.access_instruction
    if payload.is_public is not None:
        supply.is_public = payload.is_public
    _apply_map_point_update(supply.map_point, payload)
    supply.map_point.updated_by = admin.id
    if payload.items is not None:
        _replace_items(db, supply=supply, item_payloads=payload.items, now=now)
    if payload.photos is not None:
        for photo in supply.map_point.photos:
            photo.deleted_at = now
        _add_photos(db, point=supply.map_point, photos=payload.photos, uploaded_by=admin)
    supply.updated_by = admin.id
    supply.updated_at = now
    db.add(
        AdminOperationLog(
            admin_id=admin.id,
            operation_type="update",
            target_type="supply_point",
            target_id=supply.id,
            summary=f"Update supply point: {supply.name}",
            before_data=before,
            after_data={"supply_point_id": str(supply.id), "updated_at": now.isoformat()},
        )
    )
    db.commit()
    return {"supply_point_id": supply.id, "updated_at": supply.updated_at}


def soft_delete_supply_point(db: Session, *, supply_point_id: UUID, admin: User) -> dict:
    supply = get_supply_or_raise(db, supply_point_id, include_private=True)
    now = _now()
    supply.deleted_at = now
    supply.updated_at = now
    supply.updated_by = admin.id
    supply.status = "deleted"
    supply.map_point.deleted_at = now
    supply.map_point.status = "deleted"
    supply.map_point.visibility = "hidden"
    supply.map_point.updated_by = admin.id
    db.add(
        AdminOperationLog(
            admin_id=admin.id,
            operation_type="delete",
            target_type="supply_point",
            target_id=supply.id,
            summary=f"Delete supply point: {supply.name}",
            before_data={
                "supply_point_id": str(supply.id),
                "map_point_id": str(supply.map_point_id),
            },
            after_data={"deleted_at": now.isoformat()},
        )
    )
    db.commit()
    return {"supply_point_id": supply.id, "deleted_at": supply.deleted_at}


def get_supply_detail(
    db: Session,
    *,
    supply_point_id: UUID,
    include_private: bool = False,
    record_page: int = 1,
    record_page_size: int = 20,
    record_date: date | None = None,
    record_week_start: date | None = None,
    record_month: str | None = None,
) -> dict:
    supply = get_supply_or_raise(db, supply_point_id, include_private=include_private)
    return _supply_detail_payload(
        supply,
        record_page=record_page,
        record_page_size=record_page_size,
        record_date=record_date,
        record_week_start=record_week_start,
        record_month=record_month,
    )


def list_supply_records(
    db: Session,
    *,
    supply_point_id: UUID,
    page: int = 1,
    page_size: int = 20,
    record_date: date | None = None,
    record_week_start: date | None = None,
    record_month: str | None = None,
) -> dict:
    supply = get_supply_or_raise(db, supply_point_id)
    return _supply_detail_payload(
        supply,
        record_page=page,
        record_page_size=page_size,
        record_date=record_date,
        record_week_start=record_week_start,
        record_month=record_month,
    )["records"]


def _record_match_status(
    initial_items: list[SupplyPointItem],
    selected_by_id: dict[UUID, int],
) -> tuple[str, str]:
    initial_by_id = {item.id: item.quantity for item in initial_items}
    if set(initial_by_id) != set(selected_by_id):
        return "mismatch", "danger"
    for item_id, quantity in initial_by_id.items():
        if selected_by_id.get(item_id) != quantity:
            return "mismatch", "danger"
    return "matched", "success"


def create_supply_record(
    db: Session,
    *,
    supply_point_id: UUID,
    user: User,
    payload: SupplyRecordCreateRequest,
) -> dict:
    supply = get_supply_or_raise(db, supply_point_id)
    active_items = _active_items(supply)
    active_by_id = {item.id: item for item in active_items}
    selected_by_id: dict[UUID, int] = {}
    for item in payload.items:
        if item.item_id not in active_by_id:
            raise APIError(
                code=SUPPLY_ERROR_ITEM_INVALID,
                message="Supply item is invalid",
                status_code=400,
            )
        if item.item_id in selected_by_id:
            raise APIError(
                code=SUPPLY_ERROR_ITEM_INVALID,
                message="Supply item is duplicated",
                status_code=409,
            )
        selected_by_id[item.item_id] = item.quantity
    match_status, display_tone = _record_match_status(active_items, selected_by_id)
    file_id, file_url, thumbnail_url = _resolve_uploaded_file_urls(
        db,
        payload.photo,
        uploaded_by=user,
        allowed_usage_types={"supply_record_photo"},
    )
    if not file_url:
        raise APIError(
            code=SUPPLY_ERROR_PHOTO_INVALID,
            message="Supply record photo is invalid",
            status_code=400,
        )
    now = _now()
    record = SupplyPointRecord(
        supply_point_id=supply.id,
        recorder_id=user.id,
        recorded_at=now,
        match_status=match_status,
        display_tone=display_tone,
        photo_file_id=file_id,
        photo_file_url=file_url,
        photo_thumbnail_url=thumbnail_url,
        photo_cos_object_key=payload.photo.cos_object_key,
        remark=payload.remark,
    )
    record.recorder = user
    db.add(record)
    db.flush()
    for index, item_id in enumerate(selected_by_id):
        source = active_by_id[item_id]
        record_item = SupplyPointRecordItem(
            record_id=record.id,
            supply_point_item_id=source.id,
            item_name=source.item_name,
            item_type=source.item_type,
            quantity=selected_by_id[item_id],
            unit=source.unit,
            icon_key=source.icon_key,
            color_key=source.color_key,
            is_custom=source.is_custom,
            sort_order=index,
        )
        db.add(record_item)
        record.items.append(record_item)
    db.commit()
    return _record_payload(record)


def date_window_from_filter(
    *,
    record_date: date | None = None,
    record_week_start: date | None = None,
    record_month: str | None = None,
) -> tuple[datetime | None, datetime | None]:
    if record_date:
        return _start_of_day(record_date), _end_of_day(record_date)
    if record_week_start:
        week_end = date.fromordinal(record_week_start.toordinal() + 6)
        return _start_of_day(record_week_start), _end_of_day(week_end)
    if record_month:
        year, month = [int(part) for part in record_month.split("-", 1)]
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)
        return _start_of_day(start), _start_of_day(end)
    return None, None
