from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.auth.models import User
from app.modules.landmarks import service
from app.modules.landmarks.schemas import LandmarkCreateRequest, LandmarkUpdateRequest

router = APIRouter(tags=["Admin Landmarks"])


@router.post("", summary="Create a landmark point")
def create_landmark(
    payload: LandmarkCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.create_landmark(db, admin=admin, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id, message="landmark created")


@router.get("/{landmark_id}", summary="Admin get editable landmark detail")
def admin_landmark_detail(
    landmark_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.get_landmark_detail(db, landmark_id=landmark_id, include_private=True)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/{landmark_id}", summary="Update a landmark point")
def update_landmark(
    landmark_id: UUID,
    payload: LandmarkUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.update_landmark(db, landmark_id=landmark_id, admin=admin, payload=payload)
    return api_success(data=data, trace_id=request.state.trace_id, message="landmark updated")


@router.delete("/{landmark_id}", summary="Soft delete a landmark point")
def delete_landmark(
    landmark_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.soft_delete_landmark(db, landmark_id=landmark_id, admin=admin)
    return api_success(data=data, trace_id=request.state.trace_id, message="landmark deleted")
