from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.modules.auth.models import User, UserProfile
from app.modules.map import service as map_service
from app.modules.map.models import Campus, CampusArea, MapMarkerConfig, MapPoint


def create_member(
    db: Session,
    *,
    role: str = "member",
    must_change_password: bool = False,
    profile_completed: bool = True,
) -> User:
    user = User(
        student_no=f"map{uuid4().hex[:10]}",
        password_hash=hash_password("Password123"),
        role=role,
        status="active",
        must_change_password=must_change_password,
    )
    db.add(user)
    db.flush()
    db.add(
        UserProfile(
            user_id=user.id,
            nickname="地图测试成员",
            profile_completed=profile_completed,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def token_for(user: User) -> str:
    return create_access_token(
        user_id=user.id,
        student_no=user.student_no,
        role=user.role,
        token_version=user.token_version,
    )


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_for(user)}"}


def seed_map_data(db: Session) -> dict[str, MapPoint]:
    campus = Campus(
        code="hbnu_main",
        name="湖北师范大学",
        center_lng=115.062202,
        center_lat=30.229910,
        default_zoom=17,
        min_zoom=15,
        max_zoom=20,
        map_provider="amap",
    )
    db.add(campus)
    db.flush()
    north_gate = CampusArea(
        campus_id=campus.id,
        name="北门",
        area_type="gate",
        center_lng=115.060200,
        center_lat=30.233200,
        sort_order=1,
    )
    db.add(north_gate)
    marker_configs = [
        MapMarkerConfig(
            marker_key="task_emergency",
            point_type="task",
            business_type="emergency",
            label="紧急任务",
            color="#ef3038",
            z_index=100,
            default_preview_enabled=True,
            default_preview_min_zoom=16,
        ),
        MapMarkerConfig(
            marker_key="cat_home",
            point_type="cat",
            business_type="resident",
            label="猫咪点",
            color="#8754e8",
            z_index=40,
            default_preview_enabled=True,
        ),
        MapMarkerConfig(
            marker_key="supply_food",
            point_type="supply",
            business_type="food",
            label="物资点",
            color="#ff8b22",
            z_index=30,
        ),
    ]
    db.add_all(marker_configs)
    points = {
        "task": MapPoint(
            campus_id=campus.id,
            area_id=north_gate.id,
            point_type="task",
            point_scope="temporary",
            name="北门草丛紧急救助任务",
            subtitle="发现受伤流浪猫",
            description="北门草丛中发现受伤流浪猫，需要紧急救助和医疗处理。",
            location_name="北门草丛",
            location_detail="北门进门右侧草丛附近",
            lng=115.060900,
            lat=30.233000,
            geom="POINT(115.060900 30.233000)",
            route_instruction="到达北门后沿右侧小路向内走约 30 米。",
            landmark_hint="靠近北门保安亭",
            entrance_hint="从北门进入最近",
            icon_key="task_emergency",
            display_level=100,
            label_min_zoom=16,
            preview_enabled=True,
            preview_min_zoom=16,
        ),
        "cat": MapPoint(
            campus_id=campus.id,
            point_type="cat",
            point_scope="long_term",
            name="小橘常驻点",
            subtitle="教学楼B附近",
            description="常驻猫咪，性格亲人，常在教学楼B右侧草坪活动。",
            location_name="教学楼B附近",
            lng=115.063200,
            lat=30.230800,
            geom="POINT(115.063200 30.230800)",
            icon_key="cat_home",
            display_level=40,
            preview_enabled=True,
        ),
        "supply": MapPoint(
            campus_id=campus.id,
            point_type="supply",
            point_scope="long_term",
            name="猫协物资点 #1",
            subtitle="体育馆旁物资补给",
            description="猫粮、航空箱、诱捕笼备用点。",
            location_name="体育馆旁",
            lng=115.064200,
            lat=30.228700,
            geom="POINT(115.064200 30.228700)",
            icon_key="supply_food",
            display_level=30,
        ),
    }
    db.add_all(points.values())
    db.commit()
    return points


def test_map_init_returns_campus_marker_configs_and_amap_config(api_client, db_session):
    user = create_member(db_session)
    seed_map_data(db_session)

    response = api_client.get("/api/v1/map/init", headers=auth_headers(user))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["campus"]["name"] == "湖北师范大学"
    assert data["campus"]["center_lng"] == 115.062202
    assert data["areas"][0]["name"] == "北门"
    assert {item["marker_key"] for item in data["marker_configs"]} >= {
        "task_emergency",
        "cat_home",
        "supply_food",
    }
    assert data["amap_config"]["web_key"]


def test_map_points_returns_visible_markers_with_filter_and_distance(api_client, db_session):
    user = create_member(db_session)
    seed_map_data(db_session)

    response = api_client.get(
        "/api/v1/map/points?point_types=task,cat&user_lng=115.062202&user_lat=30.229910",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert [item["name"] for item in data["items"]] == [
        "北门草丛紧急救助任务",
        "小橘常驻点",
    ]
    assert data["items"][0]["business_type"] == "emergency"
    assert data["items"][0]["distance_meters"] > 0


def test_map_search_finds_points_by_keyword(api_client, db_session):
    user = create_member(db_session)
    seed_map_data(db_session)

    response = api_client.get("/api/v1/map/search?keyword=猫粮", headers=auth_headers(user))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["title"] == "猫协物资点 #1"
    assert data["items"][0]["map_point_id"]


def test_map_search_can_include_external_amap_pois(api_client, db_session, monkeypatch):
    user = create_member(db_session)
    seed_map_data(db_session)

    def fake_amap_json(path, params):
        assert path == "/v3/place/text"
        assert params["keywords"] == "教学楼"
        return {
            "status": "1",
            "pois": [
                {
                    "id": "B0FFFAKE01",
                    "name": "湖北师范大学教育大楼",
                    "type": "科教文化服务;学校;高等院校",
                    "address": "湖北省黄石市黄石港区",
                    "location": "115.061700,30.231100",
                }
            ],
        }

    monkeypatch.setattr(map_service, "_request_amap_json", fake_amap_json, raising=False)

    response = api_client.get(
        "/api/v1/map/search?keyword=教学楼&include_external=true&user_lng=115.062202&user_lat=30.229910",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    external = next(item for item in data["items"] if item["result_type"] == "external_poi")
    assert external["map_point_id"] is None
    assert external["business_id"] == "amap:B0FFFAKE01"
    assert external["title"] == "湖北师范大学教育大楼"
    assert external["lng"] == 115.0617
    assert external["distance_meters"] > 0


def test_map_summary_and_navigation_return_point_card_data(api_client, db_session):
    user = create_member(db_session)
    points = seed_map_data(db_session)
    point_id = points["task"].id

    summary = api_client.get(
        f"/api/v1/map/points/{point_id}/summary",
        headers=auth_headers(user),
    )
    navigation = api_client.get(
        f"/api/v1/map/points/{point_id}/navigation",
        headers=auth_headers(user),
    )

    assert summary.status_code == 200
    summary_data = summary.json()["data"]
    assert summary_data["title"] == "北门草丛紧急救助任务"
    assert "紧急任务" in summary_data["tags"]
    assert {action["key"] for action in summary_data["actions"]} >= {"navigate", "view_detail"}

    assert navigation.status_code == 200
    navigation_data = navigation.json()["data"]
    assert navigation_data["destination"]["lng"] == 115.0609
    assert "uri.amap.com" in navigation_data["amap_navigation"]["web_url"]


def test_map_navigation_returns_walking_route_geometry(api_client, db_session, monkeypatch):
    user = create_member(db_session)
    points = seed_map_data(db_session)
    point_id = points["task"].id

    def fake_amap_json(path, params):
        assert path == "/v3/direction/walking"
        assert params["origin"] == "115.0622,30.22991"
        assert params["destination"] == "115.0609,30.233"
        return {
            "status": "1",
            "route": {
                "paths": [
                    {
                        "distance": "450",
                        "duration": "360",
                        "steps": [
                            {
                                "instruction": "沿磁湖路向北步行",
                                "distance": "300",
                                "duration": "240",
                                "polyline": "115.0622,30.22991;115.0615,30.2314",
                            },
                            {
                                "instruction": "到达北门草丛",
                                "distance": "150",
                                "duration": "120",
                                "polyline": "115.0615,30.2314;115.0609,30.233",
                            },
                        ],
                    }
                ]
            },
        }

    monkeypatch.setattr(map_service, "_request_amap_json", fake_amap_json, raising=False)

    response = api_client.get(
        f"/api/v1/map/points/{point_id}/navigation?from_lng=115.0622&from_lat=30.22991",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    route = response.json()["data"]["route"]
    assert route["provider"] == "amap"
    assert route["fallback"] is False
    assert route["distance_meters"] == 450
    assert route["duration_seconds"] == 360
    assert route["points"] == [
        {"lng": 115.0622, "lat": 30.22991},
        {"lng": 115.0615, "lat": 30.2314},
        {"lng": 115.0609, "lat": 30.233},
    ]
    assert route["steps"][0]["instruction"] == "沿磁湖路向北步行"


def test_admin_can_edit_map_point_and_location(api_client, db_session):
    admin = create_member(db_session, role="admin")
    points = seed_map_data(db_session)
    point_id = points["task"].id

    detail = api_client.get(
        f"/api/v1/admin/map/points/{point_id}",
        headers=auth_headers(admin),
    )
    update = api_client.patch(
        f"/api/v1/admin/map/points/{point_id}",
        json={
            "name": "北门草丛救助点",
            "location_name": "北门右侧草丛",
            "route_instruction": "从北门进来后沿右侧围栏走。",
        },
        headers=auth_headers(admin),
    )
    location = api_client.patch(
        f"/api/v1/admin/map/points/{point_id}/location",
        json={"lng": 115.0611, "lat": 30.2332},
        headers=auth_headers(admin),
    )

    assert detail.status_code == 200
    assert detail.json()["data"]["name"] == "北门草丛紧急救助任务"

    assert update.status_code == 200
    assert update.json()["data"]["name"] == "北门草丛救助点"

    assert location.status_code == 200
    assert location.json()["data"]["lng"] == 115.0611
    assert location.json()["data"]["lat"] == 30.2332
    db_session.refresh(points["task"])
    assert float(points["task"].lng) == 115.0611
    assert points["task"].geom == "POINT(115.0611000 30.2332000)"


def test_member_cannot_edit_map_point(api_client, db_session):
    member = create_member(db_session)
    points = seed_map_data(db_session)

    response = api_client.patch(
        f"/api/v1/admin/map/points/{points['task'].id}/location",
        json={"lng": 115.0611, "lat": 30.2332},
        headers=auth_headers(member),
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40302


def test_map_bottom_content_returns_latest_task_items(api_client, db_session):
    user = create_member(db_session)
    seed_map_data(db_session)

    response = api_client.get("/api/v1/map/bottom-content?mode=auto", headers=auth_headers(user))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["content_type"] == "latest_tasks"
    assert data["items"][0]["title"] == "北门草丛紧急救助任务"


def test_map_endpoints_require_password_changed(api_client, db_session):
    user = create_member(db_session, must_change_password=True)
    seed_map_data(db_session)

    response = api_client.get("/api/v1/map/init", headers=auth_headers(user))

    assert response.status_code == 403
    assert response.json()["code"] == 40301


def test_map_endpoints_require_profile_completed(api_client, db_session):
    user = create_member(db_session, profile_completed=False)
    seed_map_data(db_session)

    response = api_client.get("/api/v1/map/init", headers=auth_headers(user))

    assert response.status_code == 403
    assert response.json()["code"] == 63006
