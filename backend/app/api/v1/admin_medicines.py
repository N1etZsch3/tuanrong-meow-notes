from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.auth.models import User
from app.modules.medicines import service
from app.modules.medicines.schemas import (
    MedicineArchiveRequest,
    MedicineCatalogUpdateRequest,
    MedicineCategoryCreateRequest,
    MedicineCategoryStatusRequest,
    MedicineCategoryUpdateRequest,
)

router = APIRouter(tags=["Admin Medicines"])


@router.post("/medicine-categories", summary="Create medicine category")
def create_category(
    payload: MedicineCategoryCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.create_category(db, admin=admin, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/medicine-categories/{category_id}", summary="Update medicine category")
def update_category(
    category_id: UUID,
    payload: MedicineCategoryUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.update_category(db, category_id=category_id, admin=admin, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/medicine-categories/{category_id}/status", summary="Update category status")
def update_category_status(
    category_id: UUID,
    payload: MedicineCategoryStatusRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.update_category_status(
        db,
        category_id=category_id,
        admin=admin,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/medicines/{medicine_id}", summary="Update medicine catalog")
def update_catalog(
    medicine_id: UUID,
    payload: MedicineCatalogUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.update_catalog(db, medicine_id=medicine_id, admin=admin, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/medicines/{medicine_id}/archive", summary="Archive medicine catalog")
def archive_catalog(
    medicine_id: UUID,
    payload: MedicineArchiveRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.archive_catalog(db, medicine_id=medicine_id, admin=admin, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.delete("/medicines/{medicine_id}", summary="Soft delete medicine catalog")
def delete_catalog(
    medicine_id: UUID,
    request: Request,
    reason: str = Query(min_length=1),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.delete_catalog(db, medicine_id=medicine_id, admin=admin, reason=reason)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.delete("/medicine-holdings/{holding_id}", summary="Soft delete medicine holding")
def delete_holding(
    holding_id: UUID,
    request: Request,
    reason: str = Query(min_length=1),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.delete_holding(db, holding_id=holding_id, admin=admin, reason=reason)
    return api_success(data=data, trace_id=request.state.trace_id)
