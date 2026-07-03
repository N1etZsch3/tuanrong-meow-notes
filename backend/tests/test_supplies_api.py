from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.modules.auth.models import User, UserProfile
from app.modules.map.models import Campus, MapMarkerConfig, MapPoint


def create_user(db: Session, *, role: str = "member", nickname: str = "Supply Tester") -> User:
    user = User(
        student_no=f"supply{uuid4().hex[:10]}",
        password_hash=hash_password("Password123"),
        role=role,
        status="active",
        must_change_password=False,
    )
    db.add(user)
    db.flush()
    db.add(UserProfile(user_id=user.id, nickname=nickname, profile_completed=True))
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


def seed_campus(db: Session) -> Campus:
    campus = Campus(
        code=f"supply_campus_{uuid4().hex[:8]}",
        name="Hubei Normal University",
        center_lng=115.062202,
        center_lat=30.229910,
        default_zoom=17,
        min_zoom=15,
        max_zoom=20,
        map_provider="tencent",
    )
    db.add(campus)
    db.add(
        MapMarkerConfig(
            marker_key="supply_food",
            point_type="supply",
            business_type="supply",
            label="Supply Point",
            color="#2f8f35",
            z_index=30,
            default_preview_enabled=True,
            default_preview_min_zoom=16,
            icon_width=34,
            icon_height=34,
        )
    )
    db.commit()
    db.refresh(campus)
    return campus


def supply_payload(campus: Campus) -> dict:
    return {
        "name": "Dorm A3 Supply Point",
        "description": "Long-term supply pickup point",
        "map_point": {
            "campus_id": str(campus.id),
            "lng": 115.061742,
            "lat": 30.225327,
            "location_name": "Dorm A3 Supply Point",
            "location_detail": "Behind Dorm A3",
            "route_instruction": "Walk along the dorm corridor and turn right.",
            "tencent_poi_id": "supply-poi-1",
            "tencent_poi_name": "Dorm A3",
            "tencent_poi_address": "Campus dorm area",
            "tencent_poi_category": "school:dorm",
            "tencent_poi_lng": 115.0617,
            "tencent_poi_lat": 30.2253,
            "tencent_poi_distance_meters": 12,
            "tencent_poi_match_method": "admin_selected",
        },
        "items": [
            {
                "item_name": "Cat Food",
                "item_type": "cat_food",
                "quantity": 3,
                "unit": "bag",
                "icon_key": "cat_food",
                "color_key": "green",
            },
            {
                "item_name": "Water",
                "item_type": "water",
                "quantity": 2,
                "unit": "bottle",
                "icon_key": "water",
                "color_key": "blue",
            },
            {
                "item_name": "Carrier",
                "item_type": "carrier",
                "quantity": 1,
                "unit": "box",
                "icon_key": "carrier",
                "color_key": "orange",
            },
        ],
        "photos": [
            {
                "file_url": "https://img.example.com/supply-cover.jpg",
                "thumbnail_url": "https://img.example.com/supply-cover-thumb.jpg",
                "photo_type": "cover",
                "caption": "Supply point cover",
                "sort_order": 0,
                "is_cover": True,
            }
        ],
        "is_public": True,
    }


def publish_supply_point(api_client, admin: User, campus: Campus) -> dict:
    response = api_client.post(
        "/api/v1/admin/supply-points",
        headers=auth_headers(admin),
        json=supply_payload(campus),
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_admin_can_create_supply_point_and_member_can_view_from_map(api_client, db_session):
    admin = create_user(db_session, role="admin", nickname="Manager")
    member = create_user(db_session, nickname="Member")
    campus = seed_campus(db_session)

    created = publish_supply_point(api_client, admin, campus)

    assert created["supply_point_id"]
    assert created["map_point_id"]
    assert created["initial_item_count"] == 3
    assert created["photo_count"] == 1

    point = db_session.get(MapPoint, UUID(created["map_point_id"]))
    assert point is not None
    assert point.point_type == "supply"
    assert point.name == "Dorm A3 Supply Point"
    assert point.visibility == "public"

    marker_response = api_client.get(
        "/api/v1/map/points?point_types=supply",
        headers=auth_headers(member),
    )
    assert marker_response.status_code == 200
    marker = marker_response.json()["data"]["items"][0]
    assert marker["business_id"] == created["supply_point_id"]
    assert marker["business_type"] == "supply"
    assert marker["marker_key"] == "supply_food"
    assert marker["cover_photo_url"] == "https://img.example.com/supply-cover-thumb.jpg"
    assert marker["extra"]["current_items"][0]["item_name"] == "Cat Food"

    summary_response = api_client.get(
        f"/api/v1/map/points/{created['map_point_id']}/summary",
        headers=auth_headers(member),
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()["data"]
    assert summary["business_id"] == created["supply_point_id"]
    assert summary["actions"][1]["path"] == (
        f"/pages/supplies/detail?supply_point_id={created['supply_point_id']}"
    )

    detail_response = api_client.get(
        f"/api/v1/supply-points/{created['supply_point_id']}",
        headers=auth_headers(member),
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["name"] == "Dorm A3 Supply Point"
    assert detail["current_state_source"] == "initial"
    assert [item["item_name"] for item in detail["current_items"]] == [
        "Cat Food",
        "Water",
        "Carrier",
    ]
    assert detail["records"]["items"] == []


def test_member_record_updates_latest_supply_state_and_activity_color(api_client, db_session):
    admin = create_user(db_session, role="admin", nickname="Manager")
    member = create_user(db_session, nickname="Member Nickname")
    campus = seed_campus(db_session)
    created = publish_supply_point(api_client, admin, campus)
    detail = api_client.get(
        f"/api/v1/supply-points/{created['supply_point_id']}",
        headers=auth_headers(member),
    ).json()["data"]
    cat_food_id = detail["initial_items"][0]["item_id"]
    water_id = detail["initial_items"][1]["item_id"]

    record_response = api_client.post(
        f"/api/v1/supply-points/{created['supply_point_id']}/records",
        headers=auth_headers(member),
        json={
            "items": [
                {"item_id": cat_food_id, "quantity": 3},
                {"item_id": water_id, "quantity": 2},
            ],
            "photo": {
                "file_url": "https://img.example.com/supply-record.jpg",
                "thumbnail_url": "https://img.example.com/supply-record-thumb.jpg",
            },
            "remark": "Carrier is missing.",
        },
    )

    assert record_response.status_code == 200
    record = record_response.json()["data"]
    assert record["match_status"] == "mismatch"
    assert record["display_tone"] == "danger"
    assert record["recorder"]["nickname"] == "Member Nickname"
    assert [item["item_name"] for item in record["items"]] == ["Cat Food", "Water"]

    updated_response = api_client.get(
        f"/api/v1/supply-points/{created['supply_point_id']}",
        headers=auth_headers(member),
    )

    assert updated_response.status_code == 200
    updated = updated_response.json()["data"]
    assert updated["current_state_source"] == "latest_record"
    assert [item["item_name"] for item in updated["current_items"]] == ["Cat Food", "Water"]
    assert updated["records"]["items"][0]["record_id"] == record["record_id"]
    assert updated["records"]["items"][0]["display_tone"] == "danger"


def test_record_requires_items_and_photo(api_client, db_session):
    admin = create_user(db_session, role="admin")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    created = publish_supply_point(api_client, admin, campus)

    empty_response = api_client.post(
        f"/api/v1/supply-points/{created['supply_point_id']}/records",
        headers=auth_headers(member),
        json={"items": [], "photo": None},
    )

    assert empty_response.status_code == 422


def test_admin_can_update_initial_state_without_removing_history(api_client, db_session):
    admin = create_user(db_session, role="admin", nickname="Manager")
    member = create_user(db_session, nickname="Member")
    campus = seed_campus(db_session)
    created = publish_supply_point(api_client, admin, campus)
    detail = api_client.get(
        f"/api/v1/supply-points/{created['supply_point_id']}",
        headers=auth_headers(member),
    ).json()["data"]
    first_item_id = detail["initial_items"][0]["item_id"]
    record_response = api_client.post(
        f"/api/v1/supply-points/{created['supply_point_id']}/records",
        headers=auth_headers(member),
        json={
            "items": [{"item_id": first_item_id, "quantity": 3}],
            "photo": {"file_url": "https://img.example.com/supply-record.jpg"},
        },
    )
    assert record_response.status_code == 200

    update_response = api_client.patch(
        f"/api/v1/admin/supply-points/{created['supply_point_id']}",
        headers=auth_headers(admin),
        json={
            "name": "Dorm A3 Updated Supply Point",
            "items": [
                {
                    "item_name": "Cat Food",
                    "item_type": "cat_food",
                    "quantity": 4,
                    "unit": "bag",
                    "icon_key": "cat_food",
                    "color_key": "green",
                },
                {
                    "item_name": "Gloves",
                    "item_type": "gloves",
                    "quantity": 6,
                    "unit": "pair",
                    "icon_key": "gloves",
                    "color_key": "purple",
                },
            ],
        },
    )

    assert update_response.status_code == 200
    updated = api_client.get(
        f"/api/v1/supply-points/{created['supply_point_id']}",
        headers=auth_headers(member),
    ).json()["data"]
    assert updated["name"] == "Dorm A3 Updated Supply Point"
    assert [item["item_name"] for item in updated["initial_items"]] == ["Cat Food", "Gloves"]
    assert updated["current_state_source"] == "latest_record"
    assert [item["item_name"] for item in updated["current_items"]] == ["Cat Food"]
    assert updated["records"]["total"] == 1


def test_admin_can_soft_delete_supply_point_and_hide_marker(api_client, db_session):
    admin = create_user(db_session, role="admin")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    created = publish_supply_point(api_client, admin, campus)

    delete_response = api_client.delete(
        f"/api/v1/admin/supply-points/{created['supply_point_id']}",
        headers=auth_headers(admin),
    )

    assert delete_response.status_code == 200
    point = db_session.get(MapPoint, UUID(created["map_point_id"]))
    assert point is not None
    assert point.deleted_at is not None
    assert point.visibility == "hidden"

    marker_response = api_client.get(
        "/api/v1/map/points?point_types=supply",
        headers=auth_headers(member),
    )
    assert marker_response.status_code == 200
    assert marker_response.json()["data"]["items"] == []

    detail_response = api_client.get(
        f"/api/v1/supply-points/{created['supply_point_id']}",
        headers=auth_headers(member),
    )
    assert detail_response.status_code == 404
