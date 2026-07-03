from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.me import service

router = APIRouter(tags=["Me"])


@router.get("/dashboard", summary="Get current user's personal center dashboard")
def get_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    return api_success(
        data=service.dashboard_payload(db, current_user),
        trace_id=request.state.trace_id,
    )


@router.get("/tasks", summary="List current user's tasks")
def list_my_tasks(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_profile_completed),
):
    return api_success(
        data=service.empty_page_payload(page=page, page_size=page_size),
        trace_id=request.state.trace_id,
    )


@router.get("/checkins", summary="List current user's task checkins")
def list_my_checkins(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    return api_success(
        data=service.checkins_page_payload(
            db,
            current_user,
            page=page,
            page_size=page_size,
        ),
        trace_id=request.state.trace_id,
    )


@router.get("/observations", summary="List current user's cat observations")
def list_my_observations(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_profile_completed),
):
    return api_success(
        data=service.empty_page_payload(page=page, page_size=page_size),
        trace_id=request.state.trace_id,
    )


@router.get("/favorite-cats", summary="List current user's favorite cats")
def list_my_favorite_cats(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_profile_completed),
):
    return api_success(
        data=service.empty_page_payload(page=page, page_size=page_size),
        trace_id=request.state.trace_id,
    )
