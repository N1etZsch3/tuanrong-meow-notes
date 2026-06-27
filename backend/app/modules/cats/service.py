from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.cats.models import Cat, CatAlias, CatFavorite

STATUS_LABELS = {
    "active": "正常在校",
    "missing": "暂时失踪",
    "waiting_adoption": "待领养",
    "adopted": "已领养",
    "deceased": "已死亡",
    "transferred": "转移照护",
    "archived": "归档",
}

HEALTH_STATUS_LABELS = {
    "unknown": "未知",
    "healthy": "健康",
    "watching": "需观察",
    "abnormal": "异常",
    "injured": "受伤",
    "sick": "疑似生病",
    "in_treatment": "治疗中",
    "recovered": "已恢复",
}

NEUTER_STATUS_LABELS = {
    "unknown": "未知",
    "not_neutered": "未绝育",
    "neutered": "已绝育",
    "scheduled": "已预约",
    "not_suitable": "暂不适合",
}

SORT_OPTIONS = [
    {"value": "last_seen_desc", "label": "最近出现"},
    {"value": "updated_desc", "label": "最近更新"},
    {"value": "name_asc", "label": "名称排序"},
    {"value": "health_priority", "label": "健康优先"},
    {"value": "not_neutered_first", "label": "未绝育优先"},
]

def stats(db: Session) -> dict:
    statement = select(Cat).where(Cat.deleted_at.is_(None))
    cats = db.scalars(statement).all()
    total = len(cats)
    neutered = sum(1 for cat in cats if cat.neuter_status == "neutered")
    return {
        "total_cats": total,
        "active_cats": sum(1 for cat in cats if cat.status == "active"),
        "waiting_adoption_cats": sum(1 for cat in cats if cat.status == "waiting_adoption"),
        "watching_cats": sum(1 for cat in cats if cat.health_status == "watching"),
        "neutered_cats": neutered,
        "neuter_rate": round(neutered / total * 100) if total else 0,
    }


def _option_values(mapping: dict[str, str]) -> list[dict[str, str]]:
    return [{"value": value, "label": label} for value, label in mapping.items()]


def filter_options(db: Session) -> dict:
    coat_colors = [
        value
        for value in db.scalars(
            select(Cat.coat_color)
            .where(Cat.deleted_at.is_(None))
            .distinct()
            .order_by(Cat.coat_color.asc())
        ).all()
        if value
    ]
    resident_areas = [
        value
        for value in db.scalars(
            select(Cat.resident_area_text)
            .where(Cat.deleted_at.is_(None))
            .distinct()
            .order_by(Cat.resident_area_text.asc())
        ).all()
        if value
    ]
    tags: list[str] = []
    for cat in db.scalars(select(Cat).where(Cat.deleted_at.is_(None))).all():
        tags.extend(tag for tag in (cat.personality_tags or []) if tag not in tags)

    return {
        "filter_options": [
            {"key": "status", "label": "档案状态", "values": _option_values(STATUS_LABELS)},
            {
                "key": "health_status",
                "label": "健康状态",
                "values": _option_values(HEALTH_STATUS_LABELS),
            },
            {
                "key": "neuter_status",
                "label": "绝育状态",
                "values": _option_values(NEUTER_STATUS_LABELS),
            },
            {
                "key": "coat_color",
                "label": "花色",
                "values": [{"value": item, "label": item} for item in coat_colors],
            },
            {
                "key": "resident_area",
                "label": "区域",
                "values": [{"value": item, "label": item} for item in resident_areas],
            },
            {
                "key": "personality_tag",
                "label": "性格标签",
                "values": [{"value": item, "label": item} for item in tags],
            },
            {
                "key": "last_seen_range",
                "label": "最近出现时间",
                "values": [
                    {"value": "today", "label": "今天"},
                    {"value": "three_days", "label": "三天内"},
                    {"value": "one_week", "label": "一周内"},
                    {"value": "older", "label": "一周前"},
                    {"value": "unknown", "label": "未知"},
                ],
            },
        ],
        "sort_options": SORT_OPTIONS,
    }


def _alias_summary(cat: Cat) -> str | None:
    aliases = [
        alias.alias_name
        for alias in sorted(cat.aliases, key=lambda item: (not item.is_primary, item.created_at))
        if alias.deleted_at is None
    ]
    return "、".join(aliases[:2]) if aliases else None


def _display_tags(cat: Cat) -> list[str]:
    tags: list[str] = []
    if cat.health_status in HEALTH_STATUS_LABELS and cat.health_status != "unknown":
        tags.append(HEALTH_STATUS_LABELS[cat.health_status])
    if cat.neuter_status in NEUTER_STATUS_LABELS and cat.neuter_status != "unknown":
        tags.append(NEUTER_STATUS_LABELS[cat.neuter_status])
    if cat.status != "active" and cat.status in STATUS_LABELS:
        tags.append(STATUS_LABELS[cat.status])
    for tag in cat.personality_tags or []:
        if tag not in tags:
            tags.append(tag)
        if len(tags) >= 3:
            break
    return tags[:3]


def _cat_payload(cat: Cat, favorite_cat_ids: set[UUID]) -> dict:
    return {
        "cat_id": cat.id,
        "name": cat.name,
        "avatar_url": cat.avatar_url,
        "avatar_thumbnail_url": cat.avatar_thumbnail_url,
        "coat_color": cat.coat_color,
        "alias_summary": _alias_summary(cat),
        "sex": cat.sex,
        "neuter_status": cat.neuter_status,
        "health_status": cat.health_status,
        "status": cat.status,
        "personality_tags": cat.personality_tags or [],
        "resident_area_text": cat.resident_area_text,
        "last_seen_at": cat.last_seen_at,
        "display_tags": _display_tags(cat),
        "is_favorited": cat.id in favorite_cat_ids,
    }


def _last_seen_cutoff(value: str) -> datetime | None:
    now = datetime.now(UTC)
    if value == "today":
        return now - timedelta(days=1)
    if value == "three_days":
        return now - timedelta(days=3)
    if value == "one_week":
        return now - timedelta(days=7)
    return None


def list_cats(
    db: Session,
    *,
    current_user_id: UUID,
    keyword: str | None = None,
    filter_key: str | None = None,
    filter_value: str | None = None,
    sort: str | None = "last_seen_desc",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    statement = (
        select(Cat)
        .options(selectinload(Cat.aliases))
        .where(Cat.deleted_at.is_(None))
    )
    normalized_keyword = keyword.strip() if keyword else ""
    if normalized_keyword:
        alias_match = (
            select(CatAlias.cat_id)
            .where(
                CatAlias.deleted_at.is_(None),
                CatAlias.alias_name.contains(normalized_keyword),
            )
        )
        statement = statement.where(
            or_(
                Cat.name.contains(normalized_keyword),
                Cat.coat_color.contains(normalized_keyword),
                Cat.resident_area_text.contains(normalized_keyword),
                Cat.id.in_(alias_match),
            )
        )

    tag_filter_value: str | None = None
    if filter_key and filter_value:
        if filter_key in {"status", "health_status", "neuter_status", "coat_color"}:
            statement = statement.where(getattr(Cat, filter_key) == filter_value)
        elif filter_key == "resident_area":
            statement = statement.where(Cat.resident_area_text.contains(filter_value))
        elif filter_key == "personality_tag":
            tag_filter_value = filter_value
        elif filter_key == "last_seen_range":
            cutoff = _last_seen_cutoff(filter_value)
            if filter_value == "unknown":
                statement = statement.where(Cat.last_seen_at.is_(None))
            elif filter_value == "older":
                statement = statement.where(
                    Cat.last_seen_at < datetime.now(UTC) - timedelta(days=7)
                )
            elif cutoff:
                statement = statement.where(Cat.last_seen_at >= cutoff)

    if sort == "name_asc":
        statement = statement.order_by(Cat.name.asc(), Cat.updated_at.desc())
    elif sort == "updated_desc":
        statement = statement.order_by(Cat.updated_at.desc())
    elif sort == "health_priority":
        statement = statement.order_by(Cat.updated_at.desc())
    elif sort == "not_neutered_first":
        statement = statement.order_by(Cat.updated_at.desc())
    else:
        statement = statement.order_by(Cat.last_seen_at.desc().nullslast(), Cat.updated_at.desc())

    cats = db.scalars(statement).all()
    if tag_filter_value:
        cats = [cat for cat in cats if tag_filter_value in (cat.personality_tags or [])]
    if sort == "health_priority":
        priority = {"abnormal": 0, "injured": 1, "sick": 2, "watching": 3}
        cats.sort(
            key=lambda cat: (priority.get(cat.health_status, 9), cat.updated_at),
            reverse=False,
        )
    elif sort == "not_neutered_first":
        priority = {"not_neutered": 0, "scheduled": 1, "unknown": 2}
        cats.sort(
            key=lambda cat: (priority.get(cat.neuter_status, 9), cat.updated_at),
            reverse=False,
        )

    total = len(cats)
    start = (page - 1) * page_size
    paged = cats[start : start + page_size]
    favorite_cat_ids = set(
        db.scalars(
            select(CatFavorite.cat_id).where(
                CatFavorite.user_id == current_user_id,
                CatFavorite.deleted_at.is_(None),
            )
        ).all()
    )
    return {
        "items": [_cat_payload(cat, favorite_cat_ids) for cat in paged],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": start + page_size < total,
    }
