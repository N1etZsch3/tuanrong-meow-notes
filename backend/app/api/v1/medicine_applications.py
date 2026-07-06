from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.medicines import service
from app.modules.medicines.schemas import (
    MedicineApplicationCancelRequest,
    MedicineApplicationRejectRequest,
    MedicineApplicationReviewRequest,
)

router = APIRouter(tags=["Medicine Applications"])


@router.get("", summary="List medicine applications")
def list_applications(
    request: Request,
    scope: str = Query(default="mine", pattern="^(mine|review|all)$"),
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.list_applications(
        db,
        user=current_user,
        scope=scope,
        status=status,
        page=page,
        page_size=page_size,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/{application_id}", summary="Get medicine application detail")
def application_detail(
    application_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.get_application_detail(
        db,
        application_id=application_id,
        user=current_user,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{application_id}/approve", summary="Approve medicine application")
def approve_application(
    application_id: UUID,
    payload: MedicineApplicationReviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.approve_application(
        db,
        application_id=application_id,
        user=current_user,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{application_id}/reject", summary="Reject medicine application")
def reject_application(
    application_id: UUID,
    payload: MedicineApplicationRejectRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.reject_application(
        db,
        application_id=application_id,
        user=current_user,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{application_id}/cancel", summary="Cancel medicine application")
def cancel_application(
    application_id: UUID,
    payload: MedicineApplicationCancelRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.cancel_application(
        db,
        application_id=application_id,
        user=current_user,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id)
