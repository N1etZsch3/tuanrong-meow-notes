"""Medicine holding domain: row-locked fetch, holding mutation primitives, holding admin.

`_holding_for_update_or_raise` is the single locked entry point every stock mutation and
application approval goes through. Its statement must keep `FOR UPDATE` restricted to
medicine_holdings (selectinload, not joinedload) — tests assert the compiled SQL.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import APIError
from app.modules.auth.models import User
from app.modules.medicines.common import (
    MEDICINE_ERROR_HOLDING_DELETE_NON_EMPTY,
    MEDICINE_ERROR_STOCK_NOT_ENOUGH,
    _now,
    _operation_label,
)
from app.modules.medicines.models import MedicineCatalog, MedicineHolding, MedicineStockLog


def _holding_for_update_or_raise(db: Session, holding_id: UUID) -> MedicineHolding:
    holding = db.scalar(
        select(MedicineHolding)
        .options(
            selectinload(MedicineHolding.medicine).selectinload(MedicineCatalog.category),
            selectinload(MedicineHolding.holder).selectinload(User.profile),
        )
        .where(MedicineHolding.id == holding_id, MedicineHolding.deleted_at.is_(None))
        .with_for_update(of=MedicineHolding)
    )
    if holding is None:
        raise APIError(code=66004, message="持有库存不存在", status_code=404)
    return holding


def _ensure_enough_stock(holding: MedicineHolding, quantity: Decimal) -> None:
    if quantity > holding.current_quantity:
        raise APIError(
            code=MEDICINE_ERROR_STOCK_NOT_ENOUGH,
            message="库存不足",
            status_code=409,
        )


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
