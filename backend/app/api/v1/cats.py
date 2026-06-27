from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.cats import service

router = APIRouter(tags=["Cats"])


@router.get("/stats", summary="Get cat archive stats")
def cat_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    return api_success(data=service.stats(db), trace_id=request.state.trace_id)


@router.get("/filter-options", summary="Get cat list filter options")
def cat_filter_options(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    return api_success(data=service.filter_options(db), trace_id=request.state.trace_id)


@router.get("", summary="Get cat list")
def cat_list(
    request: Request,
    keyword: str | None = Query(default=None, max_length=50),
    filter_key: str | None = Query(default=None, max_length=64),
    filter_value: str | None = Query(default=None, max_length=128),
    sort: str | None = Query(default="last_seen_desc", max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.list_cats(
        db,
        current_user_id=current_user.id,
        keyword=keyword,
        filter_key=filter_key,
        filter_value=filter_value,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return api_success(data=data, trace_id=request.state.trace_id)
