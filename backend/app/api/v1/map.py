from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.map import service

router = APIRouter(tags=["Map"])


@router.get("/init", summary="Get map initialization data")
def init_map(
    request: Request,
    campus_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.map_init(db, campus_id=campus_id)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/points", summary="Get visible map markers")
def list_points(
    request: Request,
    campus_id: UUID | None = None,
    filter_key: str | None = None,
    point_types: str | None = None,
    business_types: str | None = None,
    area_id: UUID | None = None,
    min_lng: float | None = None,
    min_lat: float | None = None,
    max_lng: float | None = None,
    max_lat: float | None = None,
    user_lng: float | None = None,
    user_lat: float | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.map_points(
        db,
        campus_id=campus_id,
        filter_key=filter_key,
        point_types=point_types,
        business_types=business_types,
        area_id=area_id,
        min_lng=min_lng,
        min_lat=min_lat,
        max_lng=max_lng,
        max_lat=max_lat,
        user_lng=user_lng,
        user_lat=user_lat,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/search", summary="Search map content")
def search_map(
    request: Request,
    keyword: str = Query(min_length=0, max_length=128),
    campus_id: UUID | None = None,
    point_types: str | None = None,
    include_external: bool = False,
    user_lng: float | None = None,
    user_lat: float | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.search(
        db,
        keyword=keyword,
        campus_id=campus_id,
        point_types=point_types,
        include_external=include_external,
        user_lng=user_lng,
        user_lat=user_lat,
        page=page,
        page_size=page_size,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/poi/resolve", summary="Resolve native Tencent POI tap")
def resolve_poi(
    request: Request,
    keyword: str = Query(default="", max_length=128),
    lng: float = Query(),
    lat: float = Query(),
    radius: int = Query(default=120, ge=10, le=1000),
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(require_profile_completed),
):
    data = service.resolve_poi(keyword=keyword, lng=lng, lat=lat, radius=radius, limit=limit)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/poi/nearby", summary="Recommend nearby Tencent POIs")
def nearby_pois(
    request: Request,
    lng: float = Query(),
    lat: float = Query(),
    keyword: str | None = Query(default=None, max_length=128),
    radius: int = Query(default=180, ge=10, le=1000),
    limit: int = Query(default=8, ge=1, le=20),
    current_user: User = Depends(require_profile_completed),
):
    data = service.nearby_pois(lng=lng, lat=lat, keyword=keyword, radius=radius, limit=limit)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/route/walking", summary="Get Tencent walking route between two coordinates")
def walking_route(
    request: Request,
    from_lng: float = Query(),
    from_lat: float = Query(),
    to_lng: float = Query(),
    to_lat: float = Query(),
    current_user: User = Depends(require_profile_completed),
):
    data = service.walking_route_between(
        from_lng=from_lng,
        from_lat=from_lat,
        to_lng=to_lng,
        to_lat=to_lat,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/points/{point_id}/summary", summary="Get map point summary card")
def point_summary(
    point_id: UUID,
    request: Request,
    user_lng: float | None = None,
    user_lat: float | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.summary(db, point_id=point_id, user_lng=user_lng, user_lat=user_lat)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/points/{point_id}/navigation", summary="Get map point navigation data")
def point_navigation(
    point_id: UUID,
    request: Request,
    from_lng: float | None = None,
    from_lat: float | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.navigation(db, point_id=point_id, from_lng=from_lng, from_lat=from_lat)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/bottom-content", summary="Get map bottom content")
def bottom_content(
    request: Request,
    mode: str = "auto",
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.bottom_content(db, mode=mode, limit=limit)
    return api_success(data=data, trace_id=request.state.trace_id)
