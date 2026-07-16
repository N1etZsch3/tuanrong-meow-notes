"""Stock operations on medicine holdings: purchase, use, scrap, adjust, distribute,
transfer.

Every operation locks the holding row (`_holding_for_update_or_raise`), mutates
quantities, appends the audit log, and commits exactly once at the end.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import APIError, ErrorCode
from app.modules.auth.models import User
from app.modules.medicines.common import _now, _parse_operated_at, _quantity
from app.modules.medicines.holding_service import (
    _append_log,
    _ensure_enough_stock,
    _holding_for_update_or_raise,
    _set_holding_quantity,
)
from app.modules.medicines.models import MedicineHolding
from app.modules.medicines.permissions import (
    _require_active_holding,
    _require_holder_or_admin,
)
from app.modules.medicines.schemas import (
    MedicineAdjustmentRequest,
    MedicineDistributeRequest,
    MedicinePurchaseRequest,
    MedicineScrapRequest,
    MedicineTransferRequest,
    MedicineUseRequest,
)


def _get_user_or_raise(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None or user.status != "active":
        raise APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="资源不存在", status_code=404)
    return user


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
