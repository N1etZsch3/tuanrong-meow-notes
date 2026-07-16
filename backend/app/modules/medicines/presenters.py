"""ORM → response payload assembly for medicines.

Presenters are pure: they never touch the database. Callers pass fully loaded rows
(holdings/logs preloaded in batch by the query service).
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.modules.auth.models import User
from app.modules.medicines.common import _operation_label, _quantity
from app.modules.medicines.models import (
    MedicineCatalog,
    MedicineCategory,
    MedicineHolding,
    MedicineStockLog,
    MedicineUseApplication,
)


def _user_payload(user: User | None) -> dict | None:
    if user is None:
        return None
    return {
        "id": str(user.id),
        "nickname": user.profile.nickname if user.profile else "未命名成员",
        "avatar_url": user.profile.avatar_url if user.profile else None,
    }


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


def _category_payload(category: MedicineCategory) -> dict:
    return {
        "id": str(category.id),
        "name": category.name,
        "code": category.code,
        "description": category.description,
        "sort_order": category.sort_order,
        "is_enabled": category.is_enabled,
    }


def _catalog_summary_payload(
    catalog: MedicineCatalog,
    *,
    holdings: list[MedicineHolding],
    current_user: User,
    recent_logs: list[MedicineStockLog] | None = None,
) -> dict:
    """Assemble the catalog summary from preloaded rows — no queries in here."""
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
        "description": catalog.description,
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
    if recent_logs is not None:
        payload["recent_logs"] = [_log_payload(log, catalog.unit) for log in recent_logs]
    return payload
