from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.auth.models import User
from app.modules.supplies import service
from app.modules.supplies.schemas import SupplyPointCreateRequest, SupplyPointUpdateRequest

router = APIRouter(tags=["Admin Supply Points"])


@router.post("", summary="Create a supply point")
def create_supply_point(
    payload: SupplyPointCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.publish_supply_point(db, admin=admin, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id, message="supply point created")


@router.get("/{supply_point_id}", summary="Admin get editable supply point detail")
def admin_supply_point_detail(
    supply_point_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.get_supply_detail(db, supply_point_id=supply_point_id, include_private=True)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/{supply_point_id}", summary="Update a supply point")
def update_supply_point(
    supply_point_id: UUID,
    payload: SupplyPointUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.update_supply_point(
        db,
        supply_point_id=supply_point_id,
        admin=admin,
        payload=payload,
    )
    return api_success(data=data, trace_id=request.state.trace_id, message="supply point updated")


@router.delete("/{supply_point_id}", summary="Soft delete a supply point")
def delete_supply_point(
    supply_point_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.soft_delete_supply_point(db, supply_point_id=supply_point_id, admin=admin)
    return api_success(data=data, trace_id=request.state.trace_id, message="supply point deleted")
