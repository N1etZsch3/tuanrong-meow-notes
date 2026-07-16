"""Medicine use-application lifecycle: create, approve, reject, cancel.

Approval deducts stock inside the same transaction as the status change, with the
holding row locked (`_holding_for_update_or_raise`) and the application row locked
(`_application_or_raise` uses FOR UPDATE restricted to the applications table).
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import APIError
from app.modules.auth.models import User
from app.modules.medicines.common import (
    MEDICINE_ERROR_APPLICATION_CHANGED,
    MEDICINE_ERROR_APPLICATION_EXPIRED,
    MEDICINE_ERROR_APPLICATION_FORBIDDEN,
    MEDICINE_ERROR_APPLICATION_NOT_FOUND,
    MEDICINE_ERROR_APPLY_TO_SELF,
    _as_aware,
    _now,
    _parse_operated_at,
    _quantity,
)
from app.modules.medicines.holding_service import (
    _append_log,
    _ensure_enough_stock,
    _holding_for_update_or_raise,
    _set_holding_quantity,
)
from app.modules.medicines.models import (
    MedicineCatalog,
    MedicineHolding,
    MedicineUseApplication,
)
from app.modules.medicines.permissions import _require_active_holding
from app.modules.medicines.schemas import (
    MedicineApplicationCancelRequest,
    MedicineApplicationCreateRequest,
    MedicineApplicationRejectRequest,
    MedicineApplicationReviewRequest,
)


def _application_or_raise(db: Session, application_id: UUID) -> MedicineUseApplication:
    application = db.scalar(
        select(MedicineUseApplication)
        .options(
            selectinload(MedicineUseApplication.medicine),
            selectinload(MedicineUseApplication.holding)
            .selectinload(MedicineHolding.medicine)
            .selectinload(MedicineCatalog.category),
            selectinload(MedicineUseApplication.holding)
            .selectinload(MedicineHolding.holder)
            .selectinload(User.profile),
            selectinload(MedicineUseApplication.applicant).selectinload(User.profile),
            selectinload(MedicineUseApplication.holder).selectinload(User.profile),
        )
        .where(
            MedicineUseApplication.id == application_id,
            MedicineUseApplication.deleted_at.is_(None),
        )
        .with_for_update(of=MedicineUseApplication)
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
