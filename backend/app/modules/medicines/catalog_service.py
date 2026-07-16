"""Medicine catalog (主档) writes: create with initial holding, edit, archive, delete."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import APIError
from app.modules.auth.models import User
from app.modules.files.service import resolve_business_image
from app.modules.medicines.category_service import (
    _get_category_or_raise,
    _resolve_category_id,
)
from app.modules.medicines.common import (
    MEDICINE_ERROR_ALREADY_HELD,
    MEDICINE_ERROR_HAS_PENDING_APPLICATION,
    MEDICINE_ERROR_HAS_STOCK,
    MEDICINE_PHOTO_LIMIT,
    _now,
    _quantity,
)
from app.modules.medicines.holding_service import _append_log
from app.modules.medicines.models import (
    MedicineCatalog,
    MedicineHolding,
    MedicinePhoto,
    MedicineStockLog,
    MedicineUseApplication,
)
from app.modules.medicines.query_service import _get_catalog_or_raise
from app.modules.medicines.schemas import (
    MedicineArchiveRequest,
    MedicineCatalogUpdateRequest,
    MedicineCreateRequest,
)


def _upsert_cover_photo(
    db: Session,
    *,
    catalog: MedicineCatalog,
    file_url: str | None,
    user: User,
    now,
) -> None:
    if not file_url:
        return

    cover_photo = db.scalar(
        select(MedicinePhoto).where(
            MedicinePhoto.medicine_id == catalog.id,
            MedicinePhoto.photo_type == "cover",
            MedicinePhoto.deleted_at.is_(None),
        ),
    )
    if cover_photo:
        cover_photo.file_url = file_url
        cover_photo.thumbnail_url = None
        cover_photo.uploaded_by = user.id
        return

    db.add(
        MedicinePhoto(
            medicine_id=catalog.id,
            file_url=file_url,
            thumbnail_url=None,
            photo_type="cover",
            caption="药品封面",
            sort_order=0,
            uploaded_by=user.id,
            created_at=now,
        ),
    )


def _catalog_photo_urls(
    *,
    cover_image_url: str | None,
    photo_urls: list[str] | None,
) -> list[str]:
    urls: list[str] = []
    if photo_urls:
        urls.extend(photo_urls)
    if cover_image_url:
        urls.insert(0, cover_image_url)

    normalized: list[str] = []
    seen: set[str] = set()
    for url in urls:
        value = url.strip()
        if not value or value in seen:
            continue
        normalized.append(value)
        seen.add(value)
        if len(normalized) >= MEDICINE_PHOTO_LIMIT:
            break
    return normalized


def _resolve_catalog_photo_urls(
    db: Session,
    *,
    photo_urls: list[str],
    user: User,
) -> list[str]:
    resolved: list[str] = []
    for file_url in photo_urls:
        _, canonical_url, _ = resolve_business_image(
            db=db,
            current_user=user,
            file_id=None,
            file_url=file_url,
            thumbnail_url=None,
            allowed_usage_types={"medicine_photo"},
        )
        if canonical_url:
            resolved.append(canonical_url)
    return resolved


def _create_catalog_photos(
    db: Session,
    *,
    catalog: MedicineCatalog,
    photo_urls: list[str],
    user: User,
    now,
) -> None:
    for index, file_url in enumerate(photo_urls):
        db.add(
            MedicinePhoto(
                medicine_id=catalog.id,
                file_url=file_url,
                thumbnail_url=None,
                photo_type="cover" if index == 0 else "gallery",
                caption="药品封面" if index == 0 else "药品照片",
                sort_order=index,
                uploaded_by=user.id,
                created_at=now,
            ),
        )


def create_medicine(db: Session, *, user: User, payload: MedicineCreateRequest) -> dict:
    now = _now()
    created_catalog = False
    if user.role in {"admin", "super_admin"}:
        holder_id = payload.holder_id or user.id
    else:
        holder_id = user.id
    if payload.medicine_id:
        catalog = _get_catalog_or_raise(db, payload.medicine_id)
        if catalog.status != "active":
            raise APIError(code=66012, message="药品已归档，不能执行该操作", status_code=409)
    else:
        assert payload.catalog is not None
        category_id = _resolve_category_id(
            db,
            category_id=payload.catalog.category_id,
            category_name=payload.catalog.category_name,
            user=user,
            now=now,
        )
        photo_urls = _catalog_photo_urls(
            cover_image_url=payload.catalog.cover_image_url,
            photo_urls=payload.catalog.photo_urls,
        )
        photo_urls = _resolve_catalog_photo_urls(db, photo_urls=photo_urls, user=user)
        cover_image_url = photo_urls[0] if photo_urls else None
        catalog = MedicineCatalog(
            name=payload.catalog.name,
            category_id=category_id,
            specification=payload.catalog.specification,
            unit=payload.catalog.unit,
            description=payload.catalog.description,
            usage_notes=payload.catalog.usage_notes,
            cover_image_url=cover_image_url,
            created_by=user.id,
            updated_by=user.id,
            created_at=now,
            updated_at=now,
        )
        db.add(catalog)
        db.flush()
        _create_catalog_photos(
            db,
            catalog=catalog,
            photo_urls=photo_urls,
            user=user,
            now=now,
        )
        created_catalog = True

    existing = db.scalar(
        select(MedicineHolding).where(
            MedicineHolding.medicine_id == catalog.id,
            MedicineHolding.holder_id == holder_id,
            MedicineHolding.deleted_at.is_(None),
            MedicineHolding.status.in_(("active", "empty")),
        )
    )
    if existing is not None:
        raise APIError(
            code=MEDICINE_ERROR_ALREADY_HELD,
            message="当前成员已持有该药品",
            status_code=409,
        )

    holding_status = "active" if payload.initial_quantity > 0 else "empty"
    holding = MedicineHolding(
        medicine_id=catalog.id,
        holder_id=holder_id,
        source_type="admin_assigned" if holder_id != user.id else "self_created",
        created_by=user.id,
        admin_creator_id=user.id if holder_id != user.id else None,
        initial_quantity=payload.initial_quantity,
        total_in_quantity=payload.initial_quantity,
        current_quantity=payload.initial_quantity,
        unit_snapshot=catalog.unit,
        status=holding_status,
        last_operation_at=now,
        remark=payload.remark,
        created_at=now,
        updated_at=now,
    )
    db.add(holding)
    db.flush()
    log = MedicineStockLog(
        medicine_id=catalog.id,
        holding_id=holding.id,
        operator_id=user.id,
        operation_type="initial_in",
        quantity_delta=payload.initial_quantity,
        quantity_before=Decimal("0"),
        quantity_after=payload.initial_quantity,
        reason_type="free_text",
        reason_text=payload.remark,
        display_title="初始入库",
        display_content=f"初始入库 {_quantity(payload.initial_quantity)}{catalog.unit}",
        operated_at=now,
        created_at=now,
    )
    db.add(log)
    db.commit()
    return {
        "medicine_id": str(catalog.id),
        "holding_id": str(holding.id),
        "created_catalog": created_catalog,
        "created_holding": True,
        "initial_stock_log_id": str(log.id),
    }


def update_catalog(
    db: Session,
    *,
    medicine_id: UUID,
    admin: User,
    payload: MedicineCatalogUpdateRequest,
) -> dict:
    catalog = _get_catalog_or_raise(db, medicine_id)
    if payload.category_id is not None:
        _get_category_or_raise(db, payload.category_id)
        catalog.category_id = payload.category_id
    elif payload.category_name is not None:
        catalog.category_id = _resolve_category_id(
            db,
            category_id=None,
            category_name=payload.category_name,
            user=admin,
            now=_now(),
        )
    if payload.name is not None:
        catalog.name = payload.name
    if payload.specification is not None:
        catalog.specification = payload.specification
    if payload.unit is not None:
        catalog.unit = payload.unit
        for holding in catalog.holdings:
            if holding.deleted_at is None:
                holding.unit_snapshot = payload.unit
    if payload.description is not None:
        catalog.description = payload.description
    if payload.usage_notes is not None:
        catalog.usage_notes = payload.usage_notes
    if payload.photo_urls is not None:
        requested_urls = _catalog_photo_urls(
            cover_image_url=payload.cover_image_url,
            photo_urls=payload.photo_urls,
        )
        resolved_urls = _resolve_catalog_photo_urls(
            db,
            photo_urls=requested_urls,
            user=admin,
        )
        replacement_time = _now()
        active_photos = db.scalars(
            select(MedicinePhoto).where(
                MedicinePhoto.medicine_id == catalog.id,
                MedicinePhoto.deleted_at.is_(None),
            )
        ).all()
        for photo in active_photos:
            photo.deleted_at = replacement_time
        catalog.cover_image_url = resolved_urls[0] if resolved_urls else None
        _create_catalog_photos(
            db,
            catalog=catalog,
            photo_urls=resolved_urls,
            user=admin,
            now=replacement_time,
        )
    elif payload.cover_image_url is not None:
        resolved_urls = _resolve_catalog_photo_urls(
            db,
            photo_urls=[payload.cover_image_url],
            user=admin,
        )
        catalog.cover_image_url = resolved_urls[0] if resolved_urls else None
        _upsert_cover_photo(
            db,
            catalog=catalog,
            file_url=catalog.cover_image_url,
            user=admin,
            now=_now(),
        )
    catalog.updated_by = admin.id
    catalog.updated_at = _now()
    db.commit()
    return {"medicine_id": str(catalog.id), "updated_at": catalog.updated_at.isoformat()}


def _total_current_quantity(db: Session, medicine_id: UUID) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(MedicineHolding.current_quantity), 0)).where(
            MedicineHolding.medicine_id == medicine_id,
            MedicineHolding.deleted_at.is_(None),
            MedicineHolding.status.in_(("active", "empty")),
        )
    )
    return Decimal(str(total or 0))


def _pending_application_count(db: Session, medicine_id: UUID) -> int:
    return int(
        db.scalar(
            select(func.count(MedicineUseApplication.id)).where(
                MedicineUseApplication.medicine_id == medicine_id,
                MedicineUseApplication.status == "pending",
                MedicineUseApplication.deleted_at.is_(None),
            )
        )
        or 0
    )


def _ensure_catalog_can_archive_or_delete(db: Session, medicine_id: UUID) -> None:
    if _total_current_quantity(db, medicine_id) > 0:
        raise APIError(
            code=MEDICINE_ERROR_HAS_STOCK,
            message="药品存在库存，不能归档或删除",
            status_code=409,
        )
    if _pending_application_count(db, medicine_id) > 0:
        raise APIError(
            code=MEDICINE_ERROR_HAS_PENDING_APPLICATION,
            message="存在待审核用药申请，不能归档或删除",
            status_code=409,
        )


def archive_catalog(
    db: Session,
    *,
    medicine_id: UUID,
    admin: User,
    payload: MedicineArchiveRequest,
) -> dict:
    catalog = _get_catalog_or_raise(db, medicine_id)
    _ensure_catalog_can_archive_or_delete(db, medicine_id)
    now = _now()
    catalog.status = "archived"
    catalog.archived_by = admin.id
    catalog.archived_at = now
    catalog.archive_reason = payload.archive_reason
    catalog.updated_by = admin.id
    catalog.updated_at = now
    _append_log(
        db,
        medicine_id=catalog.id,
        holding_id=None,
        operator_id=admin.id,
        operation_type="archive",
        quantity_delta=Decimal("0"),
        quantity_before=Decimal("0"),
        quantity_after=Decimal("0"),
        operated_at=now,
        reason_text=payload.archive_reason,
    )
    db.commit()
    return {
        "medicine_id": str(catalog.id),
        "status": catalog.status,
        "archived_at": catalog.archived_at.isoformat(),
    }


def delete_catalog(
    db: Session,
    *,
    medicine_id: UUID,
    admin: User,
    reason: str,
) -> dict:
    catalog = _get_catalog_or_raise(db, medicine_id)
    _ensure_catalog_can_archive_or_delete(db, medicine_id)
    now = _now()
    catalog.status = "deleted"
    catalog.deleted_at = now
    catalog.updated_by = admin.id
    catalog.updated_at = now
    catalog.archive_reason = reason
    db.commit()
    return {"medicine_id": str(catalog.id), "deleted_at": now.isoformat()}
