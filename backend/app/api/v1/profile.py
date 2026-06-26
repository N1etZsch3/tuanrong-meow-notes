from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_password_changed
from app.modules.auth.models import User
from app.modules.profile import service
from app.modules.profile.schemas import CompleteProfileRequest, UpdateProfileRequest

router = APIRouter(tags=["Profile"])


@router.get("/me", summary="Get current user profile")
def get_my_profile(
    request: Request,
    current_user: User = Depends(require_password_changed),
):
    return api_success(
        data=service.profile_payload(current_user),
        trace_id=request.state.trace_id,
    )


@router.post("/me/complete", summary="Complete current user profile")
def complete_my_profile(
    payload: CompleteProfileRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    data = service.complete_profile(db, current_user, payload)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/me", summary="Update current user profile")
def update_my_profile(
    payload: UpdateProfileRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    data = service.update_profile(db, current_user, payload)
    return api_success(data=data, trace_id=request.state.trace_id)
