from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.landmarks import service

router = APIRouter(tags=["Landmarks"])


@router.get("", summary="List campus landmarks")
def landmark_list(
    request: Request,
    keyword: str | None = Query(default=None, max_length=50),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.list_landmarks(db, keyword=keyword, page=page, page_size=page_size)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/{landmark_id}", summary="Get landmark detail")
def landmark_detail(
    landmark_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.get_landmark_detail(db, landmark_id=landmark_id)
    return api_success(data=data, trace_id=request.state.trace_id)
