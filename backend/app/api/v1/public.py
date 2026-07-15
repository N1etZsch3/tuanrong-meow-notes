from fastapi import APIRouter, Query, Request

from app.core.responses import api_success
from app.modules.public import service

router = APIRouter(tags=["Public"])


@router.get("/stats", summary="Get public association stats")
def public_stats(request: Request):
    data = service.get_stats().model_dump()
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/site", summary="Get public site/association info")
def public_site(request: Request):
    return api_success(data=service.get_site_info(), trace_id=request.state.trace_id)


@router.get("/cats", summary="Get public cat list")
def public_cats(
    request: Request,
    keyword: str | None = Query(default=None, max_length=50),
    coat_color: str | None = Query(default=None, max_length=32),
    sex: str | None = Query(default=None, max_length=16),
    status: str | None = Query(default=None, max_length=16),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=service.DEFAULT_PAGE_SIZE, ge=1, le=service.MAX_PAGE_SIZE),
):
    data = service.list_cats(
        keyword=keyword,
        coat_color=coat_color,
        sex=sex,
        status=status,
        page=page,
        page_size=page_size,
    ).model_dump()
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/cats/{cat_id}", summary="Get public cat detail")
def public_cat_detail(request: Request, cat_id: str):
    data = service.get_cat_detail(cat_id).model_dump()
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/posts", summary="Get public posts (trivia/merch)")
def public_posts(
    request: Request,
    type: str | None = Query(default=None, max_length=16),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=service.DEFAULT_PAGE_SIZE, ge=1, le=service.MAX_PAGE_SIZE),
):
    data = service.list_posts(post_type=type, page=page, page_size=page_size).model_dump()
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/posts/{post_id}", summary="Get public post detail")
def public_post_detail(request: Request, post_id: str):
    data = service.get_post_detail(post_id).model_dump()
    return api_success(data=data, trace_id=request.state.trace_id)
