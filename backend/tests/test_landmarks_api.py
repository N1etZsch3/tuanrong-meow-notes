from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.modules.auth.models import User, UserProfile
from app.modules.map.models import Campus, MapMarkerConfig, MapPoint


def create_user(db: Session, *, role: str = "member", nickname: str = "Landmark Tester") -> User:
    user = User(
        student_no=f"landmark{uuid4().hex[:10]}",
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
        code=f"landmark_campus_{uuid4().hex[:8]}",
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
            marker_key="landmark_library",
            point_type="landmark",
            business_type="library",
            label="地标",
            color="#28a745",
            z_index=20,
            default_preview_enabled=True,
            default_preview_min_zoom=16,
            icon_width=34,
            icon_height=34,
        )
    )
    db.commit()
    db.refresh(campus)
    return campus


def landmark_payload(campus: Campus) -> dict:
    return {
        "name": "东门地标",
        "description": "从东门进入后沿主路直行，地标位于公告栏旁。",
        "map_point": {
            "campus_id": str(campus.id),
            "lng": 115.061742,
            "lat": 30.225327,
            "location_name": "东门地标",
            "location_detail": "东门公告栏旁",
            "route_instruction": "从东门进入后沿主路直行，地标位于公告栏旁。",
            "tencent_poi_id": "landmark-poi-1",
            "tencent_poi_name": "湖北师范大学东门",
            "tencent_poi_address": "湖北师范大学",
            "tencent_poi_category": "教育学校",
            "tencent_poi_lng": 115.0617,
            "tencent_poi_lat": 30.2253,
            "tencent_poi_distance_meters": 8,
            "tencent_poi_match_method": "admin_selected",
        },
        "photos": [
            {
                "file_url": "https://img.example.com/landmark.jpg",
                "thumbnail_url": "https://img.example.com/landmark-thumb.jpg",
                "photo_type": "cover",
                "caption": "东门地标",
                "sort_order": 0,
                "is_cover": True,
            }
        ],
    }


def create_landmark(api_client, admin: User, campus: Campus) -> dict:
    response = api_client.post(
        "/api/v1/admin/landmarks",
        headers=auth_headers(admin),
        json=landmark_payload(campus),
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_admin_can_create_landmark_and_member_can_view_from_map(api_client, db_session):
    admin = create_user(db_session, role="admin", nickname="Manager")
    member = create_user(db_session, nickname="Member")
    campus = seed_campus(db_session)

    created = create_landmark(api_client, admin, campus)

    assert created["landmark_id"]
    assert created["map_point_id"] == created["landmark_id"]
    assert created["photo_count"] == 1

    point = db_session.get(MapPoint, UUID(created["map_point_id"]))
    assert point is not None
    assert point.point_type == "landmark"
    assert point.icon_key == "landmark_library"
    assert point.description == "从东门进入后沿主路直行，地标位于公告栏旁。"
    assert point.visibility == "public"

    marker_response = api_client.get(
        "/api/v1/map/points?point_types=landmark",
        headers=auth_headers(member),
    )
    assert marker_response.status_code == 200
    marker = marker_response.json()["data"]["items"][0]
    assert marker["business_id"] == created["landmark_id"]
    assert marker["business_type"] == "library"
    assert marker["marker_key"] == "landmark_library"
    assert marker["cover_photo_url"] == "https://img.example.com/landmark-thumb.jpg"

    summary_response = api_client.get(
        f"/api/v1/map/points/{created['map_point_id']}/summary",
        headers=auth_headers(member),
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()["data"]
    assert summary["business_id"] == created["landmark_id"]
    assert summary["actions"][1]["path"] == (
        f"/pages/landmarks/detail?landmark_id={created['landmark_id']}"
    )

    detail_response = api_client.get(
        f"/api/v1/landmarks/{created['landmark_id']}",
        headers=auth_headers(member),
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["name"] == "东门地标"
    assert detail["map_point"]["associated_poi"]["poi_id"] == "landmark-poi-1"
    assert detail["photos"][0]["thumbnail_url"] == "https://img.example.com/landmark-thumb.jpg"


def test_admin_can_update_and_soft_delete_landmark(api_client, db_session):
    admin = create_user(db_session, role="admin", nickname="Manager")
    member = create_user(db_session, nickname="Member")
    campus = seed_campus(db_session)
    created = create_landmark(api_client, admin, campus)

    update_response = api_client.patch(
        f"/api/v1/admin/landmarks/{created['landmark_id']}",
        headers=auth_headers(admin),
        json={
            "name": "东门公告栏",
            "description": "从东门进入即可看到公告栏。",
            "map_point": {
                "location_detail": "东门主路左侧",
                "route_instruction": "从东门进入即可看到公告栏。",
            },
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["name"] == "东门公告栏"
    assert updated["map_point"]["location_detail"] == "东门主路左侧"

    delete_response = api_client.delete(
        f"/api/v1/admin/landmarks/{created['landmark_id']}",
        headers=auth_headers(admin),
    )

    assert delete_response.status_code == 200
    point = db_session.get(MapPoint, UUID(created["map_point_id"]))
    assert point is not None
    assert point.deleted_at is not None
    assert point.visibility == "hidden"

    marker_response = api_client.get(
        "/api/v1/map/points?point_types=landmark",
        headers=auth_headers(member),
    )
    assert marker_response.status_code == 200
    assert marker_response.json()["data"]["items"] == []
