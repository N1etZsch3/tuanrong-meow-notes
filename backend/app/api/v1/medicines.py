from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.medicines import service
from app.modules.medicines.schemas import MedicineCreateRequest

router = APIRouter(tags=["Medicines"])


@router.get("", summary="List medicines")
def list_medicines(
    request: Request,
    keyword: str | None = None,
    category_id: UUID | None = None,
    holding_relation: str = "all",
    include_archived: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.list_medicines(
        db,
        user=current_user,
        keyword=keyword,
        category_id=category_id,
        holding_relation=holding_relation,
        include_archived=include_archived,
        page=page,
        page_size=page_size,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/search", summary="Search medicine catalogs")
def search_medicines(
    request: Request,
    keyword: str,
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.search_medicines(db, keyword=keyword, limit=limit)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("", summary="Create medicine or holding")
def create_medicine(
    payload: MedicineCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.create_medicine(db, user=current_user, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id, message="medicine created")


@router.get("/{medicine_id}", summary="Get medicine detail")
def medicine_detail(
    medicine_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.get_medicine_detail(db, medicine_id=medicine_id, user=current_user)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/{medicine_id}/holdings", summary="List medicine holdings")
def list_medicine_holdings(
    medicine_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.list_medicine_holdings(db, medicine_id=medicine_id, user=current_user)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/{medicine_id}/logs", summary="List medicine stock logs")
def list_medicine_logs(
    medicine_id: UUID,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.list_medicine_logs(
        db,
        medicine_id=medicine_id,
        page=page,
        page_size=page_size,
    )
    return api_success(data=data, trace_id=request.state.trace_id)
