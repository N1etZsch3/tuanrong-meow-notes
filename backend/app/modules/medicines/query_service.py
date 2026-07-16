"""Read-only medicine queries: catalog pagination, stock/application listings, details.

Nothing here writes or commits. Pagination is pushed to the database (COUNT, ORDER BY
with a unique id tiebreak, OFFSET, LIMIT) and per-page associations load in batches.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import APIError
from app.modules.auth.models import User
from app.modules.medicines.application_service import _application_or_raise
from app.modules.medicines.common import MEDICINE_ERROR_NOT_FOUND, _quantity
from app.modules.medicines.models import (
    MedicineCatalog,
    MedicineHolding,
    MedicinePhoto,
    MedicineStockLog,
    MedicineUseApplication,
)
from app.modules.medicines.presenters import (
    _application_payload,
    _catalog_summary_payload,
    _holder_payload,
    _log_payload,
    _stock_status,
    _user_payload,
)


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


def _holdings_by_medicine_ids(
    db: Session,
    medicine_ids: list[UUID],
) -> dict[UUID, list[MedicineHolding]]:
    """Load every active holding for the given catalogs in one batched query."""
    grouped: dict[UUID, list[MedicineHolding]] = {medicine_id: [] for medicine_id in medicine_ids}
    if not medicine_ids:
        return grouped
    holdings = db.scalars(
        select(MedicineHolding)
        .options(joinedload(MedicineHolding.holder).joinedload(User.profile))
        .where(
            MedicineHolding.medicine_id.in_(medicine_ids),
            MedicineHolding.deleted_at.is_(None),
            MedicineHolding.status.in_(("active", "empty")),
        )
        .order_by(
            MedicineHolding.last_operation_at.desc().nullslast(),
            MedicineHolding.created_at,
        )
    ).all()
    for holding in holdings:
        grouped[holding.medicine_id].append(holding)
    return grouped


def _photo_urls_by_medicine_ids(
    db: Session,
    medicine_ids: list[UUID],
) -> dict[UUID, list[str]]:
    """Load ordered active photos for a page of catalogs in one query."""
    grouped: dict[UUID, list[str]] = {medicine_id: [] for medicine_id in medicine_ids}
    if not medicine_ids:
        return grouped
    photos = db.scalars(
        select(MedicinePhoto)
        .where(
            MedicinePhoto.medicine_id.in_(medicine_ids),
            MedicinePhoto.deleted_at.is_(None),
        )
        .order_by(
            MedicinePhoto.medicine_id,
            MedicinePhoto.sort_order.asc(),
            MedicinePhoto.created_at.asc(),
        )
    ).all()
    for photo in photos:
        grouped[photo.medicine_id].append(photo.file_url)
    return grouped


def _catalog_list_filters(
    *,
    user: User,
    keyword: str | None,
    category_id: UUID | None,
    holding_relation: str,
    include_archived: bool,
) -> list:
    """Build the catalog list WHERE conditions, all pushable to SQL."""
    conditions = [MedicineCatalog.deleted_at.is_(None)]
    if not include_archived:
        conditions.append(MedicineCatalog.status == "active")
    if category_id:
        conditions.append(MedicineCatalog.category_id == category_id)
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                MedicineCatalog.name.ilike(like),
                MedicineCatalog.description.ilike(like),
                MedicineCatalog.usage_notes.ilike(like),
            )
        )
    if holding_relation in {"mine", "others"}:
        mine_exists = exists(
            select(MedicineHolding.id).where(
                MedicineHolding.medicine_id == MedicineCatalog.id,
                MedicineHolding.holder_id == user.id,
                MedicineHolding.deleted_at.is_(None),
                MedicineHolding.status.in_(("active", "empty")),
            )
        )
        conditions.append(mine_exists if holding_relation == "mine" else ~mine_exists)
    return conditions


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
    conditions = _catalog_list_filters(
        user=user,
        keyword=keyword,
        category_id=category_id,
        holding_relation=holding_relation,
        include_archived=include_archived,
    )
    # 数据库内完成 COUNT、排序（追加唯一 ID 保证分页稳定）与 OFFSET/LIMIT。
    total = db.scalar(
        select(func.count()).select_from(MedicineCatalog).where(*conditions)
    )
    start = (page - 1) * page_size
    page_items = db.scalars(
        select(MedicineCatalog)
        .options(joinedload(MedicineCatalog.category))
        .where(*conditions)
        .order_by(MedicineCatalog.created_at.desc(), MedicineCatalog.id.desc())
        .offset(start)
        .limit(page_size)
    ).all()
    # 当前页库存摘要：一次批量查询全部持有记录，Python 内按 medicine_id 分组聚合。
    medicine_ids = [catalog.id for catalog in page_items]
    holdings_by_medicine = _holdings_by_medicine_ids(db, medicine_ids)
    photos_by_medicine = _photo_urls_by_medicine_ids(db, medicine_ids)
    return {
        "items": [
            _catalog_summary_payload(
                catalog,
                holdings=holdings_by_medicine.get(catalog.id, []),
                photo_urls=photos_by_medicine.get(catalog.id, []),
                current_user=user,
            )
            for catalog in page_items
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
    holdings = _holdings_by_medicine_ids(db, [catalog.id]).get(catalog.id, [])
    photo_urls = _photo_urls_by_medicine_ids(db, [catalog.id]).get(catalog.id, [])
    recent_logs = db.scalars(
        select(MedicineStockLog)
        .options(joinedload(MedicineStockLog.operator).joinedload(User.profile))
        .where(MedicineStockLog.medicine_id == catalog.id)
        .order_by(MedicineStockLog.created_at.desc(), MedicineStockLog.id.desc())
        .limit(10)
    ).all()
    summary = _catalog_summary_payload(
        catalog,
        holdings=holdings,
        photo_urls=photo_urls,
        current_user=user,
        recent_logs=recent_logs,
    )
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


def _paginate_stock_logs(
    db: Session,
    *,
    conditions: list,
    unit: str,
    page: int,
    page_size: int,
) -> dict:
    """DB-paginated stock-log listing: COUNT + ORDER BY(created_at, id) + OFFSET/LIMIT."""
    total = db.scalar(
        select(func.count()).select_from(MedicineStockLog).where(*conditions)
    )
    logs = db.scalars(
        select(MedicineStockLog)
        .options(joinedload(MedicineStockLog.operator).joinedload(User.profile))
        .where(*conditions)
        .order_by(MedicineStockLog.created_at.desc(), MedicineStockLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [_log_payload(log, unit) for log in logs],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": page * page_size < total,
    }


def list_medicine_logs(
    db: Session,
    *,
    medicine_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    catalog = _get_catalog_or_raise(db, medicine_id)
    return _paginate_stock_logs(
        db,
        conditions=[MedicineStockLog.medicine_id == catalog.id],
        unit=catalog.unit,
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
    return _paginate_stock_logs(
        db,
        conditions=[MedicineStockLog.holding_id == holding.id],
        unit=holding.unit_snapshot,
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
        .order_by(MedicineStockLog.created_at.desc(), MedicineStockLog.id.desc())
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


def list_applications(
    db: Session,
    *,
    user: User,
    scope: str = "mine",
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    conditions = [MedicineUseApplication.deleted_at.is_(None)]
    if scope == "review":
        conditions.append(MedicineUseApplication.holder_id == user.id)
    elif scope == "all" and user.role in {"admin", "super_admin"}:
        pass
    elif scope == "all":
        conditions.append(
            or_(
                MedicineUseApplication.applicant_id == user.id,
                MedicineUseApplication.holder_id == user.id,
            )
        )
    else:
        conditions.append(MedicineUseApplication.applicant_id == user.id)
    if status:
        conditions.append(MedicineUseApplication.status == status)
    total = db.scalar(
        select(func.count()).select_from(MedicineUseApplication).where(*conditions)
    )
    applications = db.scalars(
        select(MedicineUseApplication)
        .options(
            joinedload(MedicineUseApplication.medicine),
            joinedload(MedicineUseApplication.holding).joinedload(MedicineHolding.holder),
            joinedload(MedicineUseApplication.applicant).joinedload(User.profile),
            joinedload(MedicineUseApplication.holder).joinedload(User.profile),
        )
        .where(*conditions)
        .order_by(
            MedicineUseApplication.created_at.desc(),
            MedicineUseApplication.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [_application_payload(application) for application in applications],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": page * page_size < total,
    }


def get_application_detail(db: Session, *, application_id: UUID, user: User) -> dict:
    application = _application_or_raise(db, application_id)
    if (
        application.applicant_id != user.id
        and application.holder_id != user.id
        and user.role not in {"admin", "super_admin"}
    ):
        raise APIError(code=40302, message="权限不足", status_code=403)
    return _application_payload(application)
