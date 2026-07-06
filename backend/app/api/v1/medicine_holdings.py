from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.medicines import service
from app.modules.medicines.schemas import (
    MedicineAdjustmentRequest,
    MedicineApplicationCreateRequest,
    MedicineDistributeRequest,
    MedicinePurchaseRequest,
    MedicineScrapRequest,
    MedicineTransferRequest,
    MedicineUseRequest,
)

router = APIRouter(tags=["Medicine Holdings"])


@router.get("/{holding_id}", summary="Get medicine holding detail")
def medicine_holding_detail(
    holding_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.get_holding_detail(db, holding_id=holding_id, user=current_user)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/{holding_id}/logs", summary="List medicine holding stock logs")
def list_holding_logs(
    holding_id: UUID,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.list_holding_logs(
        db,
        holding_id=holding_id,
        page=page,
        page_size=page_size,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{holding_id}/purchase", summary="Record medicine purchase")
def record_purchase(
    holding_id: UUID,
    payload: MedicinePurchaseRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.record_purchase(
        db,
        holding_id=holding_id,
        user=current_user,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{holding_id}/use", summary="Record medicine use")
def record_use(
    holding_id: UUID,
    payload: MedicineUseRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.record_use(db, holding_id=holding_id, user=current_user, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{holding_id}/scrap", summary="Record medicine scrap")
def record_scrap(
    holding_id: UUID,
    payload: MedicineScrapRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.record_scrap(db, holding_id=holding_id, user=current_user, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{holding_id}/adjust", summary="Adjust medicine holding stock")
def adjust_holding(
    holding_id: UUID,
    payload: MedicineAdjustmentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.adjust_holding(
        db,
        holding_id=holding_id,
        user=current_user,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{holding_id}/distribute", summary="Distribute medicine stock")
def distribute_holding(
    holding_id: UUID,
    payload: MedicineDistributeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.distribute_holding(
        db,
        holding_id=holding_id,
        user=current_user,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{holding_id}/transfer", summary="Transfer medicine stock")
def transfer_holding(
    holding_id: UUID,
    payload: MedicineTransferRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.transfer_holding(
        db,
        holding_id=holding_id,
        user=current_user,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{holding_id}/applications", summary="Create medicine use application")
def create_application(
    holding_id: UUID,
    payload: MedicineApplicationCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.create_application(
        db,
        holding_id=holding_id,
        user=current_user,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id)
