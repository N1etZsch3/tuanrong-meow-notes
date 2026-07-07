from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import APIError, ErrorCode
from app.modules.auth.models import User
from app.modules.medicines.models import (
    MedicineCatalog,
    MedicineCategory,
    MedicineHolding,
    MedicinePhoto,
    MedicineStockLog,
    MedicineUseApplication,
)
from app.modules.medicines.schemas import (
    MedicineAdjustmentRequest,
    MedicineApplicationCancelRequest,
    MedicineApplicationCreateRequest,
    MedicineApplicationRejectRequest,
    MedicineApplicationReviewRequest,
    MedicineArchiveRequest,
    MedicineCatalogUpdateRequest,
    MedicineCategoryCreateRequest,
    MedicineCategoryStatusRequest,
    MedicineCategoryUpdateRequest,
    MedicineCreateRequest,
    MedicineDistributeRequest,
    MedicinePurchaseRequest,
    MedicineScrapRequest,
    MedicineTransferRequest,
    MedicineUseRequest,
)

MEDICINE_ERROR_NOT_FOUND = 66003
MEDICINE_ERROR_CATEGORY_INVALID = 66002
MEDICINE_ERROR_ALREADY_HELD = 66009
MEDICINE_ERROR_STOCK_NOT_ENOUGH = 66005
MEDICINE_ERROR_HOLDING_FORBIDDEN = 66006
MEDICINE_ERROR_APPLICATION_NOT_FOUND = 66015
MEDICINE_ERROR_APPLICATION_FORBIDDEN = 66016
MEDICINE_ERROR_APPLICATION_CHANGED = 66017
MEDICINE_ERROR_APPLICATION_EXPIRED = 66018
MEDICINE_ERROR_APPLY_TO_SELF = 66020
MEDICINE_ERROR_HAS_STOCK = 66013
MEDICINE_ERROR_HAS_PENDING_APPLICATION = 66014
MEDICINE_ERROR_HOLDING_DELETE_NON_EMPTY = 66022
DEFAULT_CATEGORY_NAME = "其他"

DEFAULT_CATEGORIES = [
    ("抗生素", "antibiotic"),
    ("消炎药", "anti_inflammatory"),
    ("止疼药", "painkiller"),
    ("驱虫药", "deworming"),
    ("外用消毒", "external_disinfection"),
    ("眼耳用药", "eye_ear"),
    ("营养补充", "nutrition"),
    ("其他", "other"),
]
MEDICINE_PHOTO_LIMIT = 5


def _now() -> datetime:
    return datetime.now(UTC)


def _parse_operated_at(value: str | None) -> datetime:
    if not value:
        return _now()
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _as_aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _quantity(value: Decimal | int | float | None) -> int | float:
    if value is None:
        return 0
    decimal_value = Decimal(str(value))
    if decimal_value == decimal_value.to_integral_value():
        return int(decimal_value)
    return float(decimal_value)


def _stock_status(current_quantity: Decimal, total_in_quantity: Decimal) -> tuple[str, str]:
    if current_quantity <= 0:
        return "empty", "无库存"
    if total_in_quantity <= 0:
        return "sufficient", "库存充足"
    ratio = current_quantity / total_in_quantity
    if ratio < Decimal("0.2"):
        return "critical", "库存告急"
    if ratio < Decimal("0.5"):
        return "low", "库存紧张"
    return "sufficient", "库存充足"


def _upsert_cover_photo(
    db: Session,
    *,
    catalog: MedicineCatalog,
    file_url: str | None,
    user: User,
    now: datetime,
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


def _create_catalog_photos(
    db: Session,
    *,
    catalog: MedicineCatalog,
    photo_urls: list[str],
    user: User,
    now: datetime,
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


def _user_payload(user: User | None) -> dict | None:
    if user is None:
        return None
    return {
        "id": str(user.id),
        "nickname": user.profile.nickname if user.profile else "未命名成员",
        "avatar_url": user.profile.avatar_url if user.profile else None,
    }


def ensure_default_categories(db: Session, *, created_by: UUID | None = None) -> None:
    exists = db.scalar(select(func.count(MedicineCategory.id))) or 0
    if exists:
        return
    now = _now()
    for sort_order, (name, code) in enumerate(DEFAULT_CATEGORIES, start=1):
        db.add(
            MedicineCategory(
                name=name,
                code=code,
                sort_order=sort_order,
                created_by=created_by,
                created_at=now,
                updated_at=now,
            )
        )
    db.flush()


def list_categories(db: Session, *, user: User, include_disabled: bool = False) -> dict:
    ensure_default_categories(db, created_by=user.id)
    statement = select(MedicineCategory).where(MedicineCategory.deleted_at.is_(None))
    if not include_disabled:
        statement = statement.where(MedicineCategory.is_enabled.is_(True))
    categories = db.scalars(
        statement.order_by(MedicineCategory.sort_order, MedicineCategory.created_at)
    ).all()
    db.commit()
    return {
        "items": [
            {
                "id": str(category.id),
                "name": category.name,
                "code": category.code,
                "sort_order": category.sort_order,
                "is_enabled": category.is_enabled,
            }
            for category in categories
        ]
    }


def _get_category_or_raise(db: Session, category_id: UUID | None) -> MedicineCategory | None:
    if category_id is None:
        return None
    category = db.get(MedicineCategory, category_id)
    if category is None or category.deleted_at is not None or not category.is_enabled:
        raise APIError(
            code=MEDICINE_ERROR_CATEGORY_INVALID,
            message="药品分类不合法",
            status_code=400,
        )
    return category


def _resolve_category_id(
    db: Session,
    *,
    category_id: UUID | None,
    category_name: str | None,
    user: User,
    now: datetime,
) -> UUID | None:
    if category_id is not None:
        category = _get_category_or_raise(db, category_id)
        return category.id if category else None

    normalized_name = (category_name or DEFAULT_CATEGORY_NAME).strip() or DEFAULT_CATEGORY_NAME
    ensure_default_categories(db, created_by=user.id)
    category = db.scalar(
        select(MedicineCategory).where(
            func.lower(MedicineCategory.name) == normalized_name.lower(),
            MedicineCategory.deleted_at.is_(None),
        )
    )
    if category is not None:
        if not category.is_enabled:
            category.is_enabled = True
            category.updated_by = user.id
            category.updated_at = now
        return category.id

    max_sort_order = db.scalar(select(func.max(MedicineCategory.sort_order))) or 0
    category = MedicineCategory(
        name=normalized_name,
        code=None,
        sort_order=max_sort_order + 1,
        is_enabled=True,
        created_by=user.id,
        updated_by=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(category)
    db.flush()
    return category.id


def _category_payload(category: MedicineCategory) -> dict:
    return {
        "id": str(category.id),
        "name": category.name,
        "code": category.code,
        "description": category.description,
        "sort_order": category.sort_order,
        "is_enabled": category.is_enabled,
    }


def _get_catalog_or_raise(db: Session, medicine_id: UUID) -> MedicineCatalog:
    catalog = db.scalar(
        select(MedicineCatalog)
        .options(joinedload(MedicineCatalog.category))
        .where(MedicineCatalog.id == medicine_id, MedicineCatalog.deleted_at.is_(None))
    )
    if catalog is None:
        raise APIError(code=MEDICINE_ERROR_NOT_FOUND, message="药品主档不存在", status_code=404)
    return catalog


def _holding_or_raise(db: Session, holding_id: UUID) -> MedicineHolding:
    holding = db.scalar(
        select(MedicineHolding)
        .options(
            joinedload(MedicineHolding.medicine).joinedload(MedicineCatalog.category),
            joinedload(MedicineHolding.holder).joinedload(User.profile),
        )
        .where(MedicineHolding.id == holding_id, MedicineHolding.deleted_at.is_(None))
    )
    if holding is None:
        raise APIError(code=66004, message="持有库存不存在", status_code=404)
    return holding


def _holding_for_update_or_raise(db: Session, holding_id: UUID) -> MedicineHolding:
    holding = db.scalar(
        select(MedicineHolding)
        .options(
            joinedload(MedicineHolding.medicine).joinedload(MedicineCatalog.category),
            joinedload(MedicineHolding.holder).joinedload(User.profile),
        )
        .where(MedicineHolding.id == holding_id, MedicineHolding.deleted_at.is_(None))
        .with_for_update()
    )
    if holding is None:
        raise APIError(code=66004, message="持有库存不存在", status_code=404)
    return holding


def _require_active_holding(holding: MedicineHolding) -> None:
    if holding.status not in {"active", "empty"}:
        raise APIError(
            code=MEDICINE_ERROR_HOLDING_FORBIDDEN,
            message="无权操作该库存",
            status_code=403,
        )


def _require_holder_or_admin(holding: MedicineHolding, user: User) -> None:
    if holding.holder_id == user.id or user.role in {"admin", "super_admin"}:
        return
    raise APIError(
        code=MEDICINE_ERROR_HOLDING_FORBIDDEN,
        message="无权操作该库存",
        status_code=403,
    )


def _get_user_or_raise(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None or user.status != "active":
        raise APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="资源不存在", status_code=404)
    return user


def _set_holding_quantity(
    holding: MedicineHolding,
    *,
    current_quantity: Decimal,
    total_in_quantity: Decimal | None = None,
    operated_at: datetime,
) -> None:
    holding.current_quantity = current_quantity
    if total_in_quantity is not None:
        holding.total_in_quantity = total_in_quantity
    holding.status = "empty" if holding.current_quantity == 0 else "active"
    holding.last_operation_at = operated_at
    holding.updated_at = _now()


def _append_log(
    db: Session,
    *,
    medicine_id: UUID,
    holding_id: UUID | None,
    operator_id: UUID | None,
    operation_type: str,
    quantity_delta: Decimal,
    quantity_before: Decimal,
    quantity_after: Decimal,
    operated_at: datetime,
    related_application_id: UUID | None = None,
    related_task_id: UUID | None = None,
    target_user_id: UUID | None = None,
    source_holding_id: UUID | None = None,
    target_holding_id: UUID | None = None,
    reason_type: str | None = None,
    reason_text: str | None = None,
    description: str | None = None,
    remark: str | None = None,
) -> MedicineStockLog:
    log = MedicineStockLog(
        medicine_id=medicine_id,
        holding_id=holding_id,
        operator_id=operator_id,
        operation_type=operation_type,
        quantity_delta=quantity_delta,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        related_application_id=related_application_id,
        related_task_id=related_task_id,
        target_user_id=target_user_id,
        source_holding_id=source_holding_id,
        target_holding_id=target_holding_id,
        reason_type=reason_type,
        reason_text=reason_text,
        description=description,
        remark=remark,
        display_title=_operation_label(operation_type),
        display_content=description or reason_text or remark,
        operated_at=operated_at,
        created_at=_now(),
    )
    db.add(log)
    db.flush()
    return log


def _ensure_enough_stock(holding: MedicineHolding, quantity: Decimal) -> None:
    if quantity > holding.current_quantity:
        raise APIError(
            code=MEDICINE_ERROR_STOCK_NOT_ENOUGH,
            message="库存不足",
            status_code=409,
        )


def _holding_statement_for_catalog(medicine_id: UUID):
    return (
        select(MedicineHolding)
        .options(joinedload(MedicineHolding.holder).joinedload(User.profile))
        .where(
            MedicineHolding.medicine_id == medicine_id,
            MedicineHolding.deleted_at.is_(None),
            MedicineHolding.status.in_(("active", "empty")),
        )
        .order_by(MedicineHolding.last_operation_at.desc().nullslast(), MedicineHolding.created_at)
    )


def _log_payload(log: MedicineStockLog, unit: str) -> dict:
    return {
        "id": str(log.id),
        "medicine_id": str(log.medicine_id),
        "holding_id": str(log.holding_id) if log.holding_id else None,
        "operation_type": log.operation_type,
        "operation_label": _operation_label(log.operation_type),
        "operator": _user_payload(log.operator),
        "quantity_delta": _quantity(log.quantity_delta),
        "quantity_before": _quantity(log.quantity_before),
        "quantity_after": _quantity(log.quantity_after),
        "unit": unit,
        "reason_type": log.reason_type,
        "reason_text": log.reason_text,
        "description": log.description,
        "related_task": None,
        "created_at": log.created_at.isoformat(),
    }


def _paginated(items: list[dict], *, page: int, page_size: int) -> dict:
    total = len(items)
    return {
        "items": items[(page - 1) * page_size : page * page_size],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": page * page_size < total,
    }


def _application_payload(application: MedicineUseApplication) -> dict:
    medicine = application.medicine
    holding = application.holding
    return {
        "application_id": str(application.id),
        "medicine": {
            "medicine_id": str(medicine.id),
            "name": medicine.name,
            "specification": medicine.specification,
            "unit": medicine.unit,
        },
        "holding": {
            "holding_id": str(holding.id),
            "holder": _user_payload(application.holder),
            "current_quantity": _quantity(holding.current_quantity),
            "unit": holding.unit_snapshot,
        },
        "applicant": _user_payload(application.applicant),
        "holder": _user_payload(application.holder),
        "quantity": _quantity(application.quantity),
        "unit": medicine.unit,
        "reason_type": application.reason_type,
        "reason_text": application.reason_text,
        "usage_description": application.usage_description,
        "requested_use_at": application.requested_use_at.isoformat()
        if application.requested_use_at
        else None,
        "related_task": None,
        "status": application.status,
        "review_comment": application.review_comment,
        "reviewed_at": application.reviewed_at.isoformat()
        if application.reviewed_at
        else None,
        "expires_at": application.expires_at.isoformat(),
        "created_at": application.created_at.isoformat(),
        "updated_at": application.updated_at.isoformat()
        if application.updated_at
        else None,
    }


def _operation_label(operation_type: str) -> str:
    return {
        "initial_in": "初始入库",
        "purchase": "购入",
        "use_self": "使用",
        "scrap": "报废",
        "distribute_out": "分配转出",
        "distribute_in": "分配转入",
        "transfer_out": "转交转出",
        "transfer_in": "转交转入",
        "application_use": "申请使用",
        "adjustment": "库存校正",
        "archive": "归档记录",
        "delete_holding": "删除持有库存记录",
    }.get(operation_type, operation_type)


def _holder_payload(holding: MedicineHolding, current_user_id: UUID) -> dict:
    profile = holding.holder.profile if holding.holder else None
    return {
        "holding_id": str(holding.id),
        "holder_id": str(holding.holder_id),
        "holder_nickname": profile.nickname if profile else "未命名成员",
        "holder_avatar_url": profile.avatar_url if profile else None,
        "current_quantity": _quantity(holding.current_quantity),
        "unit": holding.unit_snapshot,
        "status": holding.status,
        "is_current_user_holder": holding.holder_id == current_user_id,
    }


def _catalog_summary_payload(
    db: Session,
    catalog: MedicineCatalog,
    *,
    current_user: User,
    recent_log_limit: int = 0,
) -> dict:
    holdings = db.scalars(_holding_statement_for_catalog(catalog.id)).all()
    total_current = sum((holding.current_quantity for holding in holdings), Decimal("0"))
    total_in = sum((holding.total_in_quantity for holding in holdings), Decimal("0"))
    stock_status, stock_status_label = _stock_status(total_current, total_in)
    last_operation = next(
        (holding.last_operation_at for holding in holdings if holding.last_operation_at),
        None,
    )
    payload = {
        "medicine_id": str(catalog.id),
        "name": catalog.name,
        "category": {
            "id": str(catalog.category.id),
            "name": catalog.category.name,
        }
        if catalog.category
        else None,
        "specification": catalog.specification,
        "unit": catalog.unit,
        "cover_image_url": catalog.cover_image_url,
        "status": catalog.status,
        "total_current_quantity": _quantity(total_current),
        "total_in_quantity": _quantity(total_in),
        "holder_count": len(holdings),
        "stock_status": stock_status,
        "stock_status_label": stock_status_label,
        "last_operation_at": last_operation.isoformat() if last_operation else None,
        "holders": [_holder_payload(holding, current_user.id) for holding in holdings],
    }
    if recent_log_limit:
        logs = db.scalars(
            select(MedicineStockLog)
            .options(joinedload(MedicineStockLog.operator).joinedload(User.profile))
            .where(MedicineStockLog.medicine_id == catalog.id)
            .order_by(MedicineStockLog.created_at.desc())
            .limit(recent_log_limit)
        ).all()
        payload["recent_logs"] = [_log_payload(log, catalog.unit) for log in logs]
    return payload


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
        cover_image_url = payload.catalog.cover_image_url or (photo_urls[0] if photo_urls else None)
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
        status="active",
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


def list_medicines(
    db: Session,
    *,
    user: User,
    keyword: str | None = None,
    category_id: UUID | None = None,
    holding_relation: str = "all",
    page: int = 1,
    page_size: int = 20,
    include_archived: bool = False,
) -> dict:
    statement = (
        select(MedicineCatalog)
        .options(joinedload(MedicineCatalog.category))
        .where(MedicineCatalog.deleted_at.is_(None))
    )
    if not include_archived:
        statement = statement.where(MedicineCatalog.status == "active")
    if category_id:
        statement = statement.where(MedicineCatalog.category_id == category_id)
    if keyword:
        like = f"%{keyword.strip()}%"
        statement = statement.where(
            or_(
                MedicineCatalog.name.ilike(like),
                MedicineCatalog.description.ilike(like),
                MedicineCatalog.usage_notes.ilike(like),
            )
        )
    catalogs = db.scalars(statement.order_by(MedicineCatalog.created_at.desc())).all()
    if holding_relation in {"mine", "others"}:
        filtered = []
        for catalog in catalogs:
            has_mine = db.scalar(
                select(func.count(MedicineHolding.id)).where(
                    MedicineHolding.medicine_id == catalog.id,
                    MedicineHolding.holder_id == user.id,
                    MedicineHolding.deleted_at.is_(None),
                    MedicineHolding.status.in_(("active", "empty")),
                )
            )
            if (holding_relation == "mine" and has_mine) or (
                holding_relation == "others" and not has_mine
            ):
                filtered.append(catalog)
        catalogs = filtered
    total = len(catalogs)
    start = (page - 1) * page_size
    page_items = catalogs[start : start + page_size]
    return {
        "items": [
            _catalog_summary_payload(db, catalog, current_user=user) for catalog in page_items
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": start + page_size < total,
    }


def search_medicines(db: Session, *, keyword: str, limit: int = 10) -> dict:
    statement = (
        select(MedicineCatalog)
        .options(joinedload(MedicineCatalog.category))
        .where(
            MedicineCatalog.deleted_at.is_(None),
            MedicineCatalog.status == "active",
            MedicineCatalog.name.ilike(f"%{keyword.strip()}%"),
        )
        .order_by(MedicineCatalog.name)
        .limit(limit)
    )
    catalogs = db.scalars(statement).all()
    return {
        "items": [
            {
                "medicine_id": str(catalog.id),
                "name": catalog.name,
                "category": {
                    "id": str(catalog.category.id),
                    "name": catalog.category.name,
                }
                if catalog.category
                else None,
                "category_id": str(catalog.category_id) if catalog.category_id else None,
                "category_name": catalog.category.name if catalog.category else None,
                "specification": catalog.specification,
                "unit": catalog.unit,
                "description": catalog.description,
                "usage_notes": catalog.usage_notes,
                "cover_image_url": catalog.cover_image_url,
            }
            for catalog in catalogs
        ]
    }


def get_medicine_detail(db: Session, *, medicine_id: UUID, user: User) -> dict:
    catalog = _get_catalog_or_raise(db, medicine_id)
    summary = _catalog_summary_payload(db, catalog, current_user=user, recent_log_limit=10)
    summary.update(
        {
            "description": catalog.description,
            "usage_notes": catalog.usage_notes,
            "permissions": {
                "can_edit_catalog": user.role in {"admin", "super_admin"},
                "can_archive": user.role in {"admin", "super_admin"},
                "can_delete": user.role in {"admin", "super_admin"},
            },
        }
    )
    return summary


def list_medicine_holdings(db: Session, *, medicine_id: UUID, user: User) -> dict:
    _get_catalog_or_raise(db, medicine_id)
    holdings = db.scalars(_holding_statement_for_catalog(medicine_id)).all()
    return {"items": [_holder_payload(holding, user.id) for holding in holdings]}


def list_medicine_logs(
    db: Session,
    *,
    medicine_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    catalog = _get_catalog_or_raise(db, medicine_id)
    logs = db.scalars(
        select(MedicineStockLog)
        .options(joinedload(MedicineStockLog.operator).joinedload(User.profile))
        .where(MedicineStockLog.medicine_id == catalog.id)
        .order_by(MedicineStockLog.created_at.desc())
    ).all()
    return _paginated(
        [_log_payload(log, catalog.unit) for log in logs],
        page=page,
        page_size=page_size,
    )


def list_holding_logs(
    db: Session,
    *,
    holding_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    holding = _holding_or_raise(db, holding_id)
    logs = db.scalars(
        select(MedicineStockLog)
        .options(joinedload(MedicineStockLog.operator).joinedload(User.profile))
        .where(MedicineStockLog.holding_id == holding.id)
        .order_by(MedicineStockLog.created_at.desc())
    ).all()
    return _paginated(
        [_log_payload(log, holding.unit_snapshot) for log in logs],
        page=page,
        page_size=page_size,
    )


def get_holding_detail(db: Session, *, holding_id: UUID, user: User) -> dict:
    holding = _holding_or_raise(db, holding_id)
    catalog = holding.medicine
    stock_status, _ = _stock_status(holding.current_quantity, holding.total_in_quantity)
    logs = db.scalars(
        select(MedicineStockLog)
        .options(joinedload(MedicineStockLog.operator).joinedload(User.profile))
        .where(MedicineStockLog.holding_id == holding.id)
        .order_by(MedicineStockLog.created_at.desc())
        .limit(10)
    ).all()
    is_holder = holding.holder_id == user.id
    can_mutate = is_holder and holding.status in {"active", "empty"}
    pending_applications = db.scalars(
        select(MedicineUseApplication)
        .options(
            joinedload(MedicineUseApplication.medicine),
            joinedload(MedicineUseApplication.holding).joinedload(MedicineHolding.holder),
            joinedload(MedicineUseApplication.applicant).joinedload(User.profile),
            joinedload(MedicineUseApplication.holder).joinedload(User.profile),
        )
        .where(
            MedicineUseApplication.holding_id == holding.id,
            MedicineUseApplication.status == "pending",
            MedicineUseApplication.deleted_at.is_(None),
        )
        .order_by(MedicineUseApplication.created_at.desc())
    ).all()
    return {
        "holding_id": str(holding.id),
        "medicine": {
            "medicine_id": str(catalog.id),
            "name": catalog.name,
            "category_name": catalog.category.name if catalog.category else None,
            "specification": catalog.specification,
            "unit": catalog.unit,
            "description": catalog.description,
            "usage_notes": catalog.usage_notes,
            "cover_image_url": catalog.cover_image_url,
        },
        "holder": _user_payload(holding.holder),
        "initial_quantity": _quantity(holding.initial_quantity),
        "total_in_quantity": _quantity(holding.total_in_quantity),
        "current_quantity": _quantity(holding.current_quantity),
        "unit": holding.unit_snapshot,
        "status": holding.status,
        "stock_status": stock_status,
        "last_operation_at": holding.last_operation_at.isoformat()
        if holding.last_operation_at
        else None,
        "recent_logs": [_log_payload(log, catalog.unit) for log in logs],
        "pending_applications": [
            {
                "id": str(application.id),
                "medicine_id": str(application.medicine_id),
                "medicine_name": application.medicine.name,
                "holding_id": str(application.holding_id),
                "quantity": _quantity(application.quantity),
                "unit": catalog.unit,
                "reason_text": application.reason_text,
                "usage_description": application.usage_description,
                "status": application.status,
                "expires_at": application.expires_at.isoformat(),
                "created_at": application.created_at.isoformat(),
            }
            for application in pending_applications
        ],
        "permissions": {
            "is_holder": is_holder,
            "can_record": can_mutate,
            "can_apply": (
                (not is_holder)
                and holding.status == "active"
                and holding.current_quantity > 0
            ),
            "can_review_application": can_mutate,
        },
    }


def record_purchase(
    db: Session,
    *,
    holding_id: UUID,
    user: User,
    payload: MedicinePurchaseRequest,
) -> dict:
    holding = _holding_for_update_or_raise(db, holding_id)
    _require_active_holding(holding)
    _require_holder_or_admin(holding, user)
    operated_at = _parse_operated_at(payload.operated_at)
    before = holding.current_quantity
    after = before + payload.quantity
    total_in = holding.total_in_quantity + payload.quantity
    _set_holding_quantity(
        holding,
        current_quantity=after,
        total_in_quantity=total_in,
        operated_at=operated_at,
    )
    log = _append_log(
        db,
        medicine_id=holding.medicine_id,
        holding_id=holding.id,
        operator_id=user.id,
        operation_type="purchase",
        quantity_delta=payload.quantity,
        quantity_before=before,
        quantity_after=after,
        operated_at=operated_at,
        reason_type="free_text",
        reason_text=payload.source,
        remark=payload.remark,
    )
    db.commit()
    return {
        "holding_id": str(holding.id),
        "current_quantity": _quantity(after),
        "total_in_quantity": _quantity(total_in),
        "stock_log_id": str(log.id),
    }


def record_use(
    db: Session,
    *,
    holding_id: UUID,
    user: User,
    payload: MedicineUseRequest,
) -> dict:
    holding = _holding_for_update_or_raise(db, holding_id)
    _require_active_holding(holding)
    _require_holder_or_admin(holding, user)
    _ensure_enough_stock(holding, payload.quantity)
    operated_at = _parse_operated_at(payload.operated_at)
    before = holding.current_quantity
    after = before - payload.quantity
    _set_holding_quantity(holding, current_quantity=after, operated_at=operated_at)
    log = _append_log(
        db,
        medicine_id=holding.medicine_id,
        holding_id=holding.id,
        operator_id=user.id,
        operation_type="use_self",
        quantity_delta=-payload.quantity,
        quantity_before=before,
        quantity_after=after,
        operated_at=operated_at,
        related_task_id=payload.related_task_id,
        reason_type=payload.reason_type,
        reason_text=payload.reason_text,
        description=payload.usage_description,
        remark=payload.remark,
    )
    db.commit()
    return {
        "holding_id": str(holding.id),
        "current_quantity": _quantity(after),
        "stock_log_id": str(log.id),
    }


def record_scrap(
    db: Session,
    *,
    holding_id: UUID,
    user: User,
    payload: MedicineScrapRequest,
) -> dict:
    holding = _holding_for_update_or_raise(db, holding_id)
    _require_active_holding(holding)
    _require_holder_or_admin(holding, user)
    _ensure_enough_stock(holding, payload.quantity)
    operated_at = _parse_operated_at(payload.operated_at)
    before = holding.current_quantity
    after = before - payload.quantity
    _set_holding_quantity(holding, current_quantity=after, operated_at=operated_at)
    log = _append_log(
        db,
        medicine_id=holding.medicine_id,
        holding_id=holding.id,
        operator_id=user.id,
        operation_type="scrap",
        quantity_delta=-payload.quantity,
        quantity_before=before,
        quantity_after=after,
        operated_at=operated_at,
        reason_type=payload.reason_type,
        reason_text=payload.reason_text,
        remark=payload.remark,
    )
    db.commit()
    return {
        "holding_id": str(holding.id),
        "current_quantity": _quantity(after),
        "stock_log_id": str(log.id),
    }


def adjust_holding(
    db: Session,
    *,
    holding_id: UUID,
    user: User,
    payload: MedicineAdjustmentRequest,
) -> dict:
    holding = _holding_for_update_or_raise(db, holding_id)
    _require_active_holding(holding)
    _require_holder_or_admin(holding, user)
    operated_at = _parse_operated_at(payload.operated_at)
    before = holding.current_quantity
    after = payload.quantity
    total_in = max(holding.total_in_quantity, after)
    _set_holding_quantity(
        holding,
        current_quantity=after,
        total_in_quantity=total_in,
        operated_at=operated_at,
    )
    log = _append_log(
        db,
        medicine_id=holding.medicine_id,
        holding_id=holding.id,
        operator_id=user.id,
        operation_type="adjustment",
        quantity_delta=after - before,
        quantity_before=before,
        quantity_after=after,
        operated_at=operated_at,
        reason_type="inventory_check",
        reason_text=payload.reason_text,
        remark=payload.remark,
    )
    db.commit()
    return {
        "holding_id": str(holding.id),
        "current_quantity": _quantity(after),
        "total_in_quantity": _quantity(total_in),
        "stock_log_id": str(log.id),
    }


def _target_holding_for_distribution(
    db: Session,
    *,
    source: MedicineHolding,
    target_user_id: UUID,
    creator_id: UUID,
    operated_at: datetime,
) -> MedicineHolding:
    target = db.scalar(
        select(MedicineHolding)
        .where(
            MedicineHolding.medicine_id == source.medicine_id,
            MedicineHolding.holder_id == target_user_id,
            MedicineHolding.deleted_at.is_(None),
            MedicineHolding.status.in_(("active", "empty")),
        )
        .with_for_update()
    )
    if target is not None:
        return target
    target = MedicineHolding(
        medicine_id=source.medicine_id,
        holder_id=target_user_id,
        source_type="distributed",
        source_holding_id=source.id,
        created_by=creator_id,
        initial_quantity=Decimal("0"),
        total_in_quantity=Decimal("0"),
        current_quantity=Decimal("0"),
        unit_snapshot=source.unit_snapshot,
        status="empty",
        last_operation_at=operated_at,
        created_at=operated_at,
        updated_at=operated_at,
    )
    db.add(target)
    db.flush()
    return target


def distribute_holding(
    db: Session,
    *,
    holding_id: UUID,
    user: User,
    payload: MedicineDistributeRequest,
) -> dict:
    source = _holding_for_update_or_raise(db, holding_id)
    _require_active_holding(source)
    _require_holder_or_admin(source, user)
    if payload.target_user_id == source.holder_id:
        raise APIError(code=40001, message="不能分配给自己", status_code=400)
    _get_user_or_raise(db, payload.target_user_id)
    _ensure_enough_stock(source, payload.quantity)
    operated_at = _parse_operated_at(payload.operated_at)
    target = _target_holding_for_distribution(
        db,
        source=source,
        target_user_id=payload.target_user_id,
        creator_id=user.id,
        operated_at=operated_at,
    )
    source_before = source.current_quantity
    source_after = source_before - payload.quantity
    target_before = target.current_quantity
    target_after = target_before + payload.quantity
    _set_holding_quantity(source, current_quantity=source_after, operated_at=operated_at)
    _set_holding_quantity(
        target,
        current_quantity=target_after,
        total_in_quantity=target.total_in_quantity + payload.quantity,
        operated_at=operated_at,
    )
    out_log = _append_log(
        db,
        medicine_id=source.medicine_id,
        holding_id=source.id,
        operator_id=user.id,
        operation_type="distribute_out",
        quantity_delta=-payload.quantity,
        quantity_before=source_before,
        quantity_after=source_after,
        target_user_id=payload.target_user_id,
        target_holding_id=target.id,
        operated_at=operated_at,
        remark=payload.remark,
    )
    in_log = _append_log(
        db,
        medicine_id=source.medicine_id,
        holding_id=target.id,
        operator_id=user.id,
        operation_type="distribute_in",
        quantity_delta=payload.quantity,
        quantity_before=target_before,
        quantity_after=target_after,
        source_holding_id=source.id,
        target_user_id=payload.target_user_id,
        operated_at=operated_at,
        remark=payload.remark,
    )
    db.commit()
    return {
        "source_holding_id": str(source.id),
        "target_holding_id": str(target.id),
        "source_current_quantity": _quantity(source_after),
        "target_current_quantity": _quantity(target_after),
        "out_log_id": str(out_log.id),
        "in_log_id": str(in_log.id),
    }


def transfer_holding(
    db: Session,
    *,
    holding_id: UUID,
    user: User,
    payload: MedicineTransferRequest,
) -> dict:
    source = _holding_for_update_or_raise(db, holding_id)
    _require_active_holding(source)
    _require_holder_or_admin(source, user)
    if payload.target_user_id == source.holder_id:
        raise APIError(code=40001, message="不能转交给自己", status_code=400)
    _get_user_or_raise(db, payload.target_user_id)
    operated_at = _parse_operated_at(payload.operated_at)
    quantity = source.current_quantity
    target = db.scalar(
        select(MedicineHolding)
        .where(
            MedicineHolding.medicine_id == source.medicine_id,
            MedicineHolding.holder_id == payload.target_user_id,
            MedicineHolding.deleted_at.is_(None),
            MedicineHolding.status.in_(("active", "empty")),
        )
        .with_for_update()
    )
    source_before = source.current_quantity
    if target is None:
        source.holder_id = payload.target_user_id
        source.source_type = "transferred"
        source.last_operation_at = operated_at
        source.updated_at = _now()
        target = source
        source_after = source.current_quantity
        target_before = source_before
        target_after = source.current_quantity
    else:
        target_before = target.current_quantity
        target_after = target_before + quantity
        source.current_quantity = Decimal("0")
        source.status = "transferred"
        source.last_operation_at = operated_at
        source.updated_at = _now()
        _set_holding_quantity(
            target,
            current_quantity=target_after,
            total_in_quantity=target.total_in_quantity + quantity,
            operated_at=operated_at,
        )
        source_after = Decimal("0")
    out_log = _append_log(
        db,
        medicine_id=source.medicine_id,
        holding_id=source.id,
        operator_id=user.id,
        operation_type="transfer_out",
        quantity_delta=-quantity if target.id != source.id else Decimal("0"),
        quantity_before=source_before,
        quantity_after=source_after,
        target_user_id=payload.target_user_id,
        target_holding_id=target.id,
        operated_at=operated_at,
        reason_text=payload.reason,
    )
    in_log = _append_log(
        db,
        medicine_id=source.medicine_id,
        holding_id=target.id,
        operator_id=user.id,
        operation_type="transfer_in",
        quantity_delta=quantity if target.id != source.id else Decimal("0"),
        quantity_before=target_before,
        quantity_after=target_after,
        source_holding_id=source.id,
        target_user_id=payload.target_user_id,
        operated_at=operated_at,
        reason_text=payload.reason,
    )
    db.commit()
    return {
        "source_holding_id": str(source.id),
        "target_holding_id": str(target.id),
        "transferred_quantity": _quantity(quantity),
        "target_current_quantity": _quantity(target_after),
        "out_log_id": str(out_log.id),
        "in_log_id": str(in_log.id),
    }


def create_application(
    db: Session,
    *,
    holding_id: UUID,
    user: User,
    payload: MedicineApplicationCreateRequest,
) -> dict:
    holding = _holding_for_update_or_raise(db, holding_id)
    _require_active_holding(holding)
    if holding.holder_id == user.id:
        raise APIError(
            code=MEDICINE_ERROR_APPLY_TO_SELF,
            message="不能向自己持有的库存提交申请",
            status_code=403,
        )
    _ensure_enough_stock(holding, payload.quantity)
    now = _now()
    application = MedicineUseApplication(
        medicine_id=holding.medicine_id,
        holding_id=holding.id,
        applicant_id=user.id,
        holder_id=holding.holder_id,
        quantity=payload.quantity,
        reason_type=payload.reason_type,
        reason_text=payload.reason_text,
        usage_description=payload.usage_description,
        requested_use_at=_parse_operated_at(payload.requested_use_at),
        related_task_id=payload.related_task_id,
        status="pending",
        expires_at=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )
    db.add(application)
    db.commit()
    return {
        "application_id": str(application.id),
        "status": application.status,
        "expires_at": application.expires_at.isoformat(),
    }


def list_applications(
    db: Session,
    *,
    user: User,
    scope: str = "mine",
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    statement = (
        select(MedicineUseApplication)
        .options(
            joinedload(MedicineUseApplication.medicine),
            joinedload(MedicineUseApplication.holding).joinedload(MedicineHolding.holder),
            joinedload(MedicineUseApplication.applicant).joinedload(User.profile),
            joinedload(MedicineUseApplication.holder).joinedload(User.profile),
        )
        .where(MedicineUseApplication.deleted_at.is_(None))
    )
    if scope == "review":
        statement = statement.where(MedicineUseApplication.holder_id == user.id)
    elif scope == "all" and user.role in {"admin", "super_admin"}:
        pass
    elif scope == "all":
        statement = statement.where(
            or_(
                MedicineUseApplication.applicant_id == user.id,
                MedicineUseApplication.holder_id == user.id,
            )
        )
    else:
        statement = statement.where(MedicineUseApplication.applicant_id == user.id)
    if status:
        statement = statement.where(MedicineUseApplication.status == status)
    applications = db.scalars(
        statement.order_by(MedicineUseApplication.created_at.desc())
    ).all()
    return _paginated(
        [_application_payload(application) for application in applications],
        page=page,
        page_size=page_size,
    )


def get_application_detail(db: Session, *, application_id: UUID, user: User) -> dict:
    application = _application_or_raise(db, application_id)
    if (
        application.applicant_id != user.id
        and application.holder_id != user.id
        and user.role not in {"admin", "super_admin"}
    ):
        raise APIError(code=40302, message="权限不足", status_code=403)
    return _application_payload(application)


def _application_or_raise(db: Session, application_id: UUID) -> MedicineUseApplication:
    application = db.scalar(
        select(MedicineUseApplication)
        .options(
            joinedload(MedicineUseApplication.medicine),
            joinedload(MedicineUseApplication.holding)
            .joinedload(MedicineHolding.medicine)
            .joinedload(MedicineCatalog.category),
            joinedload(MedicineUseApplication.holding)
            .joinedload(MedicineHolding.holder)
            .joinedload(User.profile),
            joinedload(MedicineUseApplication.applicant).joinedload(User.profile),
            joinedload(MedicineUseApplication.holder).joinedload(User.profile),
        )
        .where(
            MedicineUseApplication.id == application_id,
            MedicineUseApplication.deleted_at.is_(None),
        )
        .with_for_update()
    )
    if application is None:
        raise APIError(
            code=MEDICINE_ERROR_APPLICATION_NOT_FOUND,
            message="用药申请不存在",
            status_code=404,
        )
    return application


def _require_pending_application(application: MedicineUseApplication) -> None:
    if application.status != "pending":
        raise APIError(
            code=MEDICINE_ERROR_APPLICATION_CHANGED,
            message="用药申请状态已变化",
            status_code=409,
        )


def _require_not_expired(application: MedicineUseApplication) -> None:
    if _as_aware(application.expires_at) <= _now():
        application.status = "expired"
        application.updated_at = _now()
        raise APIError(
            code=MEDICINE_ERROR_APPLICATION_EXPIRED,
            message="用药申请已过期",
            status_code=409,
        )


def approve_application(
    db: Session,
    *,
    application_id: UUID,
    user: User,
    payload: MedicineApplicationReviewRequest,
) -> dict:
    application = _application_or_raise(db, application_id)
    if application.holder_id != user.id:
        raise APIError(
            code=MEDICINE_ERROR_APPLICATION_FORBIDDEN,
            message="无权审核该用药申请",
            status_code=403,
        )
    _require_pending_application(application)
    _require_not_expired(application)
    holding = _holding_for_update_or_raise(db, application.holding_id)
    _ensure_enough_stock(holding, application.quantity)
    operated_at = _parse_operated_at(payload.operated_at)
    before = holding.current_quantity
    after = before - application.quantity
    _set_holding_quantity(holding, current_quantity=after, operated_at=operated_at)
    log = _append_log(
        db,
        medicine_id=holding.medicine_id,
        holding_id=holding.id,
        operator_id=user.id,
        operation_type="application_use",
        quantity_delta=-application.quantity,
        quantity_before=before,
        quantity_after=after,
        related_application_id=application.id,
        related_task_id=application.related_task_id,
        reason_type=application.reason_type,
        reason_text=application.reason_text,
        description=application.usage_description,
        remark=payload.review_comment,
        operated_at=operated_at,
    )
    application.status = "approved"
    application.reviewer_id = user.id
    application.review_comment = payload.review_comment
    application.reviewed_at = operated_at
    application.stock_log_id = log.id
    application.updated_at = _now()
    db.commit()
    return {
        "application_id": str(application.id),
        "status": application.status,
        "holding_id": str(holding.id),
        "current_quantity": _quantity(after),
        "stock_log_id": str(log.id),
    }


def reject_application(
    db: Session,
    *,
    application_id: UUID,
    user: User,
    payload: MedicineApplicationRejectRequest,
) -> dict:
    application = _application_or_raise(db, application_id)
    if application.holder_id != user.id:
        raise APIError(
            code=MEDICINE_ERROR_APPLICATION_FORBIDDEN,
            message="无权审核该用药申请",
            status_code=403,
        )
    _require_pending_application(application)
    application.status = "rejected"
    application.reviewer_id = user.id
    application.review_comment = payload.review_comment
    application.reviewed_at = _now()
    application.updated_at = _now()
    db.commit()
    return {"application_id": str(application.id), "status": application.status}


def cancel_application(
    db: Session,
    *,
    application_id: UUID,
    user: User,
    payload: MedicineApplicationCancelRequest,
) -> dict:
    application = _application_or_raise(db, application_id)
    if application.applicant_id != user.id:
        raise APIError(code=40302, message="权限不足", status_code=403)
    _require_pending_application(application)
    application.status = "cancelled"
    application.review_comment = payload.cancel_reason
    application.cancelled_at = _now()
    application.updated_at = _now()
    db.commit()
    return {"application_id": str(application.id), "status": application.status}


def create_category(
    db: Session,
    *,
    admin: User,
    payload: MedicineCategoryCreateRequest,
) -> dict:
    category = MedicineCategory(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        sort_order=payload.sort_order,
        is_enabled=True,
        created_by=admin.id,
        updated_by=admin.id,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return _category_payload(category)


def update_category(
    db: Session,
    *,
    category_id: UUID,
    admin: User,
    payload: MedicineCategoryUpdateRequest,
) -> dict:
    category = _get_category_or_raise(db, category_id)
    if payload.name is not None:
        category.name = payload.name
    if payload.code is not None:
        category.code = payload.code
    if payload.description is not None:
        category.description = payload.description
    if payload.sort_order is not None:
        category.sort_order = payload.sort_order
    category.updated_by = admin.id
    category.updated_at = _now()
    db.commit()
    db.refresh(category)
    return _category_payload(category)


def update_category_status(
    db: Session,
    *,
    category_id: UUID,
    admin: User,
    payload: MedicineCategoryStatusRequest,
) -> dict:
    category = _get_category_or_raise(db, category_id)
    category.is_enabled = payload.is_enabled
    category.updated_by = admin.id
    category.updated_at = _now()
    db.commit()
    db.refresh(category)
    return _category_payload(category)


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
    if payload.cover_image_url is not None:
        catalog.cover_image_url = payload.cover_image_url
        _upsert_cover_photo(
            db,
            catalog=catalog,
            file_url=payload.cover_image_url,
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


def delete_holding(
    db: Session,
    *,
    holding_id: UUID,
    admin: User,
    reason: str,
) -> dict:
    holding = _holding_for_update_or_raise(db, holding_id)
    if holding.current_quantity > 0:
        raise APIError(
            code=MEDICINE_ERROR_HOLDING_DELETE_NON_EMPTY,
            message="持有库存不能直接删除，请先转交或清空",
            status_code=409,
        )
    now = _now()
    holding.status = "deleted"
    holding.deleted_at = now
    holding.deleted_by = admin.id
    holding.delete_reason = reason
    holding.updated_at = now
    log = _append_log(
        db,
        medicine_id=holding.medicine_id,
        holding_id=holding.id,
        operator_id=admin.id,
        operation_type="delete_holding",
        quantity_delta=Decimal("0"),
        quantity_before=Decimal("0"),
        quantity_after=Decimal("0"),
        operated_at=now,
        reason_text=reason,
    )
    db.commit()
    return {
        "holding_id": str(holding.id),
        "deleted_at": now.isoformat(),
        "stock_log_id": str(log.id),
    }
