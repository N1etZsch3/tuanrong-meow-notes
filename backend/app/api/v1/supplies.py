from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.supplies import service
from app.modules.supplies.schemas import SupplyRecordCreateRequest

router = APIRouter(tags=["Supply Points"])


@router.get("/{supply_point_id}", summary="Get supply point detail")
def supply_point_detail(
    supply_point_id: UUID,
    request: Request,
    record_date: date | None = None,
    record_week_start: date | None = None,
    record_month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    record_page: int = Query(default=1, ge=1),
    record_page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.get_supply_detail(
        db,
        supply_point_id=supply_point_id,
        record_page=record_page,
        record_page_size=record_page_size,
        record_date=record_date,
        record_week_start=record_week_start,
        record_month=record_month,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/{supply_point_id}/records", summary="List supply point records")
def list_supply_point_records(
    supply_point_id: UUID,
    request: Request,
    record_date: date | None = None,
    record_week_start: date | None = None,
    record_month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.list_supply_records(
        db,
        supply_point_id=supply_point_id,
        page=page,
        page_size=page_size,
        record_date=record_date,
        record_week_start=record_week_start,
        record_month=record_month,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/{supply_point_id}/records", summary="Record current supply point state")
def create_supply_point_record(
    supply_point_id: UUID,
    payload: SupplyRecordCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.create_supply_record(
        db,
        supply_point_id=supply_point_id,
        user=current_user,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id, message="supply record created")
