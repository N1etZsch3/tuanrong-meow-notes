"""Medicine category management: default seeding, listing, admin CRUD."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import APIError
from app.modules.auth.models import User
from app.modules.medicines.common import (
    DEFAULT_CATEGORIES,
    DEFAULT_CATEGORY_NAME,
    MEDICINE_ERROR_CATEGORY_INVALID,
    _now,
)
from app.modules.medicines.models import MedicineCategory
from app.modules.medicines.presenters import _category_payload
from app.modules.medicines.schemas import (
    MedicineCategoryCreateRequest,
    MedicineCategoryStatusRequest,
    MedicineCategoryUpdateRequest,
)


def ensure_default_categories(db: Session, *, created_by: UUID | None = None) -> bool:
    exists_count = db.scalar(select(func.count(MedicineCategory.id))) or 0
    if exists_count:
        return False
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
    return True


def list_categories(db: Session, *, user: User, include_disabled: bool = False) -> dict:
    # 首次访问时补种默认分类（写），只有确实播种过才提交；常态请求保持只读。
    if ensure_default_categories(db, created_by=user.id):
        db.commit()
    statement = select(MedicineCategory).where(MedicineCategory.deleted_at.is_(None))
    if not include_disabled:
        statement = statement.where(MedicineCategory.is_enabled.is_(True))
    categories = db.scalars(
        statement.order_by(MedicineCategory.sort_order, MedicineCategory.created_at)
    ).all()
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
    now,
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
