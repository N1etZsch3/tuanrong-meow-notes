import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.errors import APIError, ErrorCode
from app.modules.public.schemas import (
    PublicCatDetail,
    PublicCatList,
    PublicCatListItem,
    PublicPostCard,
    PublicPostDetail,
    PublicPostList,
    PublicStats,
)

MOCK_DATA_DIR = Path(__file__).resolve().parent / "mock_data"

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20
VALID_POST_TYPES = {"trivia", "merch"}


@lru_cache
def _load_fixture(name: str) -> Any:
    with open(MOCK_DATA_DIR / name, encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _paginate(items: list[Any], page: int, page_size: int) -> tuple[list[Any], int, bool]:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    has_more = end < total
    return page_items, total, has_more


def get_stats() -> PublicStats:
    return PublicStats.model_validate(_load_fixture("stats.json"))


def get_site_info() -> dict[str, Any]:
    return dict(_load_fixture("site.json"))


def _cat_list_item(raw: dict[str, Any]) -> PublicCatListItem:
    aliases = raw.get("aliases") or []
    return PublicCatListItem(
        cat_id=raw["cat_id"],
        name=raw["name"],
        avatar_url=raw.get("avatar_url"),
        coat_color=raw["coat_color"],
        sex=raw["sex"],
        neuter_status=raw["neuter_status"],
        status=raw["status"],
        personality_tags=raw.get("personality_tags") or [],
        alias_summary="、".join(aliases) if aliases else None,
    )


def list_cats(
    *,
    keyword: str | None = None,
    coat_color: str | None = None,
    sex: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> PublicCatList:
    cats: list[dict[str, Any]] = list(_load_fixture("cats.json"))

    if keyword:
        needle = keyword.strip().lower()
        cats = [
            cat
            for cat in cats
            if needle in cat["name"].lower()
            or any(needle in alias.lower() for alias in (cat.get("aliases") or []))
        ]
    if coat_color:
        cats = [cat for cat in cats if cat["coat_color"] == coat_color]
    if sex:
        cats = [cat for cat in cats if cat["sex"] == sex]
    if status:
        cats = [cat for cat in cats if cat["status"] == status]

    page_items, total, has_more = _paginate(cats, page, page_size)
    return PublicCatList(
        items=[_cat_list_item(cat) for cat in page_items],
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


def get_cat_detail(cat_id: str) -> PublicCatDetail:
    for cat in _load_fixture("cats.json"):
        if cat["cat_id"] == cat_id:
            return PublicCatDetail.model_validate(cat)
    raise APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="猫咪不存在", status_code=404)


def list_posts(
    *,
    post_type: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> PublicPostList:
    if post_type is not None and post_type not in VALID_POST_TYPES:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="内容类型无效", status_code=400)

    posts: list[dict[str, Any]] = list(_load_fixture("posts.json"))
    if post_type:
        posts = [post for post in posts if post["post_type"] == post_type]

    page_items, total, has_more = _paginate(posts, page, page_size)
    return PublicPostList(
        items=[PublicPostCard.model_validate(post) for post in page_items],
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


def get_post_detail(post_id: str) -> PublicPostDetail:
    for post in _load_fixture("posts.json"):
        if post["post_id"] == post_id:
            return PublicPostDetail.model_validate(post)
    raise APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="内容不存在", status_code=404)
