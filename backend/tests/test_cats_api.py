from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.security import create_access_token, hash_password
from app.modules.auth.models import User, UserProfile
from app.modules.cats.models import Cat, CatAlias, CatFavorite


def create_member(
    db,
    *,
    must_change_password: bool = False,
    profile_completed: bool = True,
) -> User:
    user = User(
        student_no=f"cat{uuid4().hex[:10]}",
        password_hash=hash_password("Password123"),
        role="member",
        status="active",
        must_change_password=must_change_password,
    )
    db.add(user)
    db.flush()
    db.add(
        UserProfile(
            user_id=user.id,
            nickname="猫咪库测试成员",
            profile_completed=profile_completed,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        user_id=user.id,
        student_no=user.student_no,
        role=user.role,
        token_version=user.token_version,
    )
    return {"Authorization": f"Bearer {token}"}


def test_cats_empty_list_contract(api_client, db_session):
    user = create_member(db_session)

    stats_response = api_client.get("/api/v1/cats/stats", headers=auth_headers(user))
    filters_response = api_client.get(
        "/api/v1/cats/filter-options",
        headers=auth_headers(user),
    )
    list_response = api_client.get("/api/v1/cats", headers=auth_headers(user))

    assert stats_response.status_code == 200
    assert stats_response.json()["data"] == {
        "total_cats": 0,
        "active_cats": 0,
        "waiting_adoption_cats": 0,
        "adopted_cats": 0,
        "deceased_cats": 0,
        "watching_cats": 0,
        "neutered_cats": 0,
        "neuter_rate": 0,
    }

    assert filters_response.status_code == 200
    filter_data = filters_response.json()["data"]
    assert [item["key"] for item in filter_data["filter_options"]] == [
        "status",
        "health_status",
        "neuter_status",
        "coat_color",
        "resident_area",
        "personality_tag",
        "last_seen_range",
    ]
    assert filter_data["sort_options"][0] == {
        "value": "last_seen_desc",
        "label": "最近出现",
    }

    assert list_response.status_code == 200
    assert list_response.json()["data"] == {
        "items": [],
        "page": 1,
        "page_size": 20,
        "total": 0,
        "has_more": False,
    }


def seed_cat(
    db,
    *,
    name: str,
    coat_color: str,
    resident_area_text: str,
    health_status: str = "healthy",
    neuter_status: str = "unknown",
    status: str = "active",
    personality_tags: list[str] | None = None,
    last_seen_at: datetime | None = None,
    alias: str | None = None,
) -> Cat:
    cat = Cat(
        name=name,
        avatar_url=f"/uploads/cats/{name}.jpg",
        avatar_thumbnail_url=f"/uploads/cats/{name}_thumb.jpg",
        coat_color=coat_color,
        sex="unknown",
        neuter_status=neuter_status,
        health_status=health_status,
        status=status,
        resident_area_text=resident_area_text,
        personality_tags=personality_tags or ["警惕"],
        last_seen_at=last_seen_at,
    )
    db.add(cat)
    db.flush()
    if alias:
        db.add(CatAlias(cat_id=cat.id, alias_name=alias, is_primary=True))
    db.commit()
    db.refresh(cat)
    return cat


def test_cats_list_search_filter_stats_and_favorites(api_client, db_session):
    user = create_member(db_session)
    now = datetime.now(UTC)
    xiaoju = seed_cat(
        db_session,
        name="小橘",
        coat_color="橘猫",
        resident_area_text="学生宿舍区",
        health_status="healthy",
        neuter_status="neutered",
        personality_tags=["亲人", "贪吃"],
        last_seen_at=now,
        alias="橘子",
    )
    seed_cat(
        db_session,
        name="台阶狸花",
        coat_color="狸花",
        resident_area_text="教学楼A",
        health_status="watching",
        neuter_status="unknown",
        personality_tags=["警惕"],
        last_seen_at=now - timedelta(hours=1),
    )
    seed_cat(
        db_session,
        name="北门警长",
        coat_color="狸花",
        resident_area_text="北门",
        health_status="watching",
        neuter_status="not_neutered",
        status="waiting_adoption",
        personality_tags=["胆小"],
        last_seen_at=None,
    )
    seed_cat(
        db_session,
        name="领养团子",
        coat_color="橘猫",
        resident_area_text="北门",
        health_status="healthy",
        neuter_status="neutered",
        status="adopted",
        personality_tags=["贪吃"],
        last_seen_at=now - timedelta(days=2),
    )
    seed_cat(
        db_session,
        name="毕业花花",
        coat_color="狸花",
        resident_area_text="教学楼A",
        health_status="recovered",
        neuter_status="neutered",
        status="deceased",
        personality_tags=["警惕"],
        last_seen_at=now - timedelta(days=3),
    )
    db_session.add(CatFavorite(user_id=user.id, cat_id=xiaoju.id))
    db_session.commit()

    stats_response = api_client.get("/api/v1/cats/stats", headers=auth_headers(user))
    list_response = api_client.get("/api/v1/cats?page=1&page_size=2", headers=auth_headers(user))
    alias_response = api_client.get("/api/v1/cats?keyword=橘子", headers=auth_headers(user))
    filter_response = api_client.get(
        "/api/v1/cats?filter_key=health_status&filter_value=watching&sort=not_neutered_first",
        headers=auth_headers(user),
    )
    tag_response = api_client.get(
        "/api/v1/cats?filter_key=personality_tag&filter_value=亲人",
        headers=auth_headers(user),
    )
    options_response = api_client.get("/api/v1/cats/filter-options", headers=auth_headers(user))

    assert stats_response.status_code == 200
    assert stats_response.json()["data"] == {
        "total_cats": 5,
        "active_cats": 2,
        "waiting_adoption_cats": 1,
        "adopted_cats": 1,
        "deceased_cats": 1,
        "watching_cats": 2,
        "neutered_cats": 3,
        "neuter_rate": 60,
    }

    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert list_data["total"] == 5
    assert list_data["has_more"] is True
    assert [item["name"] for item in list_data["items"]] == ["小橘", "台阶狸花"]
    assert list_data["items"][0]["alias_summary"] == "橘子"
    assert list_data["items"][0]["display_tags"] == ["健康", "已绝育", "亲人"]
    assert list_data["items"][0]["is_favorited"] is True

    assert alias_response.status_code == 200
    assert [item["name"] for item in alias_response.json()["data"]["items"]] == ["小橘"]

    assert filter_response.status_code == 200
    assert [item["name"] for item in filter_response.json()["data"]["items"]] == [
        "北门警长",
        "台阶狸花",
    ]

    assert tag_response.status_code == 200
    assert [item["name"] for item in tag_response.json()["data"]["items"]] == ["小橘"]

    option_values = {
        item["key"]: [value["value"] for value in item["values"]]
        for item in options_response.json()["data"]["filter_options"]
    }
    assert option_values["coat_color"] == ["橘猫", "狸花"]
    assert option_values["resident_area"] == ["北门", "学生宿舍区", "教学楼A"]
    assert option_values["personality_tag"] == ["亲人", "贪吃", "警惕", "胆小"]


def test_cats_endpoints_require_profile_completed(api_client, db_session):
    user = create_member(db_session, profile_completed=False)

    response = api_client.get("/api/v1/cats", headers=auth_headers(user))

    assert response.status_code == 403
    assert response.json()["code"] == 63006


def test_cats_list_pages_do_not_overlap_or_drop_with_identical_sort_keys(
    api_client, db_session
):
    user = create_member(db_session)
    shared_seen = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)
    for index in range(25):
        seed_cat(
            db_session,
            name=f"猫{index:02d}",
            coat_color="狸花",
            resident_area_text="教学楼A",
            last_seen_at=shared_seen,
        )
    db_session.commit()

    collected: list[str] = []
    for page in range(1, 5):
        response = api_client.get(
            f"/api/v1/cats?page={page}&page_size=10",
            headers=auth_headers(user),
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 25
        collected.extend(item["cat_id"] for item in data["items"])

    assert len(collected) == 25
    assert len(set(collected)) == 25
