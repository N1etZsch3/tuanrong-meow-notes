from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.modules.auth.models import User, UserProfile
from app.modules.map.models import Campus, MapMarkerConfig
from app.modules.tasks import service as task_service


def create_user(
    db: Session,
    *,
    role: str = "member",
    nickname: str = "任务测试成员",
) -> User:
    user = User(
        student_no=f"task{uuid4().hex[:10]}",
        password_hash=hash_password("Password123"),
        role=role,
        status="active",
        must_change_password=False,
    )
    db.add(user)
    db.flush()
    db.add(
        UserProfile(
            user_id=user.id,
            nickname=nickname,
            profile_completed=True,
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


def seed_campus(db: Session) -> Campus:
    campus = Campus(
        code=f"task_campus_{uuid4().hex[:8]}",
        name="湖北师范大学",
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
            marker_key="task_feeding",
            point_type="task",
            business_type="feeding",
            label="喂食任务",
            color="#2f8f35",
            z_index=80,
            default_preview_enabled=True,
            default_preview_min_zoom=16,
            icon_width=34,
            icon_height=34,
        )
    )
    db.commit()
    db.refresh(campus)
    return campus


def publish_payload(campus: Campus) -> dict:
    return {
        "title": "学生宿舍区北侧喂食点",
        "description": "暑假投喂，注意清理食盆周边。",
        "required_items": "猫粮、水",
        "map_point": {
            "campus_id": str(campus.id),
            "lng": 115.06321,
            "lat": 30.23108,
            "location_name": "学生宿舍区北侧",
            "location_detail": "靠近教学楼B后方草坪",
            "route_instruction": "到达教学楼B后沿右侧小路进入。",
            "landmark_hint": "教学楼B",
            "entrance_hint": "从宿舍区北侧小路进入最近",
            "tencent_poi_id": "7554185223751732838",
            "tencent_poi_name": "湖北师范大学教育大楼",
            "tencent_poi_address": "湖北省黄石市黄石港区",
            "tencent_poi_category": "教育学校:大学",
            "tencent_poi_lng": 115.0617,
            "tencent_poi_lat": 30.2311,
            "tencent_poi_distance_meters": 42,
            "tencent_poi_match_method": "admin_selected",
        },
        "execute_dates": ["2026-07-02", "2026-07-09", "2026-07-16"],
        "photos": [
            {
                "file_id": None,
                "file_url": "https://img.example.com/task-feeding.jpg",
                "thumbnail_url": "https://img.example.com/task-feeding-thumb.jpg",
                "photo_type": "cover",
                "caption": "喂食点现场图",
                "sort_order": 0,
                "is_cover": True,
            }
        ],
        "is_public": True,
    }


def publish_task(api_client, admin: User, campus: Campus) -> dict:
    response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(admin),
        json=publish_payload(campus),
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_admin_can_publish_summer_feeding_task_and_map_marker_is_visible(
    api_client,
    db_session,
):
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)

    data = publish_task(api_client, admin, campus)

    assert data["task_type"] == "feeding"
    assert data["task_mode"] == "recurring"
    assert data["schedule_type"] == "selected_dates"
    assert data["completion_policy"] == "per_execution_date"
    assert data["status"] == "in_progress"
    assert data["execution_date_count"] == 3
    assert data["photo_count"] == 1
    assert data["map_point_id"]

    map_response = api_client.get(
        "/api/v1/map/points?point_types=task&business_types=feeding",
        headers=auth_headers(member),
    )

    assert map_response.status_code == 200
    marker = map_response.json()["data"]["items"][0]
    assert marker["name"] == "学生宿舍区北侧喂食点"
    assert marker["business_type"] == "feeding"
    assert marker["business_id"] == data["task_id"]
    assert marker["marker_key"] == "task_feeding"
    assert marker["cover_photo_url"] == "https://img.example.com/task-feeding-thumb.jpg"
    assert marker["extra"]["location_detail"] == "靠近教学楼B后方草坪"
    assert marker["extra"]["task_status_label"] == "进行中"
    assert marker["extra"]["next_execute_date"] == "2026-07-02"
    assert marker["extra"]["associated_poi"]["poi_id"] == "7554185223751732838"


def test_map_point_summary_uses_uploaded_task_photos_for_detail_thumbnails(
    api_client,
    db_session,
):
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    payload = publish_payload(campus)
    payload["photos"].extend(
        [
            {
                "file_id": None,
                "file_url": "https://img.example.com/task-feeding-2.jpg",
                "thumbnail_url": "https://img.example.com/task-feeding-2-thumb.jpg",
                "photo_type": "scene",
                "caption": "喂食点补充图",
                "sort_order": 1,
                "is_cover": False,
            },
            {
                "file_id": None,
                "file_url": "https://img.example.com/task-feeding-3.jpg",
                "thumbnail_url": "https://img.example.com/task-feeding-3-thumb.jpg",
                "photo_type": "route",
                "caption": "入口路线图",
                "sort_order": 2,
                "is_cover": False,
            },
        ]
    )

    publish_response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(admin),
        json=payload,
    )
    assert publish_response.status_code == 200
    published = publish_response.json()["data"]

    summary_response = api_client.get(
        f"/api/v1/map/points/{published['map_point_id']}/summary",
        headers=auth_headers(member),
    )

    assert summary_response.status_code == 200
    summary = summary_response.json()["data"]
    assert summary["cover_photo_url"] == "https://img.example.com/task-feeding-thumb.jpg"
    assert [photo["thumbnail_url"] for photo in summary["photos"]] == [
        "https://img.example.com/task-feeding-thumb.jpg",
        "https://img.example.com/task-feeding-2-thumb.jpg",
        "https://img.example.com/task-feeding-3-thumb.jpg",
    ]


def test_member_list_and_detail_include_dates_photos_location_materials_and_activities(
    api_client,
    db_session,
):
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session, nickname="Nietzsche")
    campus = seed_campus(db_session)
    published = publish_task(api_client, admin, campus)

    list_response = api_client.get("/api/v1/tasks", headers=auth_headers(member))
    detail_response = api_client.get(
        f"/api/v1/tasks/{published['task_id']}",
        headers=auth_headers(member),
    )

    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert list_data["total"] == 1
    item = list_data["items"][0]
    assert item["title"] == "学生宿舍区北侧喂食点"
    assert item["required_items"] == "猫粮、水"
    assert item["cover_photo_url"] == "https://img.example.com/task-feeding-thumb.jpg"
    assert item["date_range"]["total_count"] == 3
    assert item["next_execution"]["execute_date"] == "2026-07-02"

    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["title"] == "学生宿舍区北侧喂食点"
    assert detail["description"] == "暑假投喂，注意清理食盆周边。"
    assert detail["required_items"] == "猫粮、水"
    assert detail["map_point"]["route_instruction"] == "到达教学楼B后沿右侧小路进入。"
    assert detail["map_point"]["lng"] == 115.06321
    assert detail["map_point"]["lat"] == 30.23108
    assert detail["map_point"]["associated_poi"] == {
        "provider": "tencent",
        "poi_id": "7554185223751732838",
        "name": "湖北师范大学教育大楼",
        "address": "湖北省黄石市黄石港区",
        "category": "教育学校:大学",
        "lng": 115.0617,
        "lat": 30.2311,
        "distance_meters": 42,
        "match_method": "admin_selected",
    }
    assert detail["photos"][0]["is_cover"] is True
    assert [item["execute_date"] for item in detail["execution_dates"]] == [
        "2026-07-02",
        "2026-07-09",
        "2026-07-16",
    ]
    assert detail["activities"][0]["activity_type"] == "created"
    assert detail["actions"]["can_navigate"] is True
    assert detail["actions"]["can_admin_edit"] is False


def test_admin_can_get_editable_task_detail_with_dates_point_and_photos(
    api_client,
    db_session,
):
    admin = create_user(db_session, role="admin", nickname="管理员")
    campus = seed_campus(db_session)
    published = publish_task(api_client, admin, campus)

    response = api_client.get(
        f"/api/v1/admin/tasks/{published['task_id']}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["task_id"] == published["task_id"]
    assert data["title"] == "学生宿舍区北侧喂食点"
    assert data["actions"]["can_admin_edit"] is True
    assert data["map_point"]["map_point_id"] == published["map_point_id"]
    assert data["map_point"]["lng"] == 115.06321
    assert [item["execute_date"] for item in data["execution_dates"]] == [
        "2026-07-02",
        "2026-07-09",
        "2026-07-16",
    ]
    assert data["photos"][0]["file_url"] == "https://img.example.com/task-feeding.jpg"


def test_member_checkin_completes_one_execution_date_without_completing_parent_task(
    api_client,
    db_session,
):
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session, nickname="Nietzsche")
    campus = seed_campus(db_session)
    published = publish_task(api_client, admin, campus)

    response = api_client.post(
        f"/api/v1/tasks/{published['task_id']}/checkins",
        headers=auth_headers(member),
        json={
            "execute_date": "2026-07-02",
            "is_completed": True,
            "process_result": "已补充猫粮和水",
            "remark": "现场正常",
            "checkin_lng": 115.06322,
            "checkin_lat": 30.23109,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["execute_date"] == "2026-07-02"
    assert data["checkin"]["process_result"] == "已补充猫粮和水"

    detail_response = api_client.get(
        f"/api/v1/tasks/{published['task_id']}",
        headers=auth_headers(member),
    )
    detail = detail_response.json()["data"]
    assert detail["status"] == "in_progress"
    assert detail["date_range"]["completed_count"] == 1
    assert detail["date_range"]["pending_count"] == 2
    assert detail["execution_dates"][0]["status"] == "completed"
    assert detail["activities"][0]["activity_type"] == "execution_completed"


def test_member_list_filters_by_execution_status_instead_of_parent_task_status(
    api_client,
    db_session,
):
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session, nickname="Nietzsche")
    campus = seed_campus(db_session)
    today = date.today().isoformat()

    first_payload = publish_payload(campus)
    first_payload["execute_dates"] = [today]
    first_response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(admin),
        json=first_payload,
    )
    assert first_response.status_code == 200
    completed_task_id = first_response.json()["data"]["task_id"]

    second_payload = publish_payload(campus)
    second_payload["title"] = "待投喂任务"
    second_payload["execute_dates"] = [today]
    second_payload["map_point"]["lng"] = 115.06421
    second_payload["map_point"]["lat"] = 30.23158
    second_response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(admin),
        json=second_payload,
    )
    assert second_response.status_code == 200
    pending_task_id = second_response.json()["data"]["task_id"]

    checkin_response = api_client.post(
        f"/api/v1/tasks/{completed_task_id}/checkins",
        headers=auth_headers(member),
        json={"execute_date": today, "is_completed": True},
    )
    assert checkin_response.status_code == 200

    pending_response = api_client.get(
        f"/api/v1/tasks?execute_date={today}&execution_status=pending&status=in_progress,completed",
        headers=auth_headers(member),
    )
    assert pending_response.status_code == 200
    pending_items = pending_response.json()["data"]["items"]
    assert [item["task_id"] for item in pending_items] == [pending_task_id]
    assert pending_items[0]["current_execution"]["status"] == "pending"

    completed_response = api_client.get(
        f"/api/v1/tasks?execute_date={today}&execution_status=completed&status=in_progress,completed",
        headers=auth_headers(member),
    )
    assert completed_response.status_code == 200
    completed_items = completed_response.json()["data"]["items"]
    assert [item["task_id"] for item in completed_items] == [completed_task_id]
    assert completed_items[0]["current_execution"]["status"] == "completed"


def test_member_list_filters_by_execution_date_range(api_client, db_session):
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    published = publish_task(api_client, admin, campus)

    july_response = api_client.get(
        "/api/v1/tasks?execute_date_start=2026-07-01&execute_date_end=2026-07-31",
        headers=auth_headers(member),
    )
    assert july_response.status_code == 200
    assert [item["task_id"] for item in july_response.json()["data"]["items"]] == [
        published["task_id"]
    ]

    august_response = api_client.get(
        "/api/v1/tasks?execute_date_start=2026-08-01&execute_date_end=2026-08-31",
        headers=auth_headers(member),
    )
    assert august_response.status_code == 200
    assert august_response.json()["data"]["items"] == []


def test_future_execution_date_is_not_checkable_before_that_day(
    api_client,
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        task_service,
        "_now",
        lambda: datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
    )
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    payload = publish_payload(campus)
    payload["execute_dates"] = ["2026-07-09"]

    publish_response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(admin),
        json=payload,
    )
    assert publish_response.status_code == 200
    task_id = publish_response.json()["data"]["task_id"]

    detail_response = api_client.get(
        f"/api/v1/tasks/{task_id}?current_date=2026-07-02",
        headers=auth_headers(member),
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["current_execution"]["execute_date"] == "2026-07-09"
    assert detail["actions"]["can_checkin"] is False
    assert detail["actions"]["checkin_disabled_reason"] == "未到任务日期"

    checkin_response = api_client.post(
        f"/api/v1/tasks/{task_id}/checkins",
        headers=auth_headers(member),
        json={"execute_date": "2026-07-09", "is_completed": True},
    )
    assert checkin_response.status_code == 400
    assert checkin_response.json()["code"] == 62007


def test_completion_activity_content_uses_actual_completed_date(
    api_client,
    db_session,
    monkeypatch,
):
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session, nickname="Nietzsche")
    campus = seed_campus(db_session)
    payload = publish_payload(campus)
    payload["execute_dates"] = ["2026-07-02"]
    publish_response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(admin),
        json=payload,
    )
    assert publish_response.status_code == 200
    task_id = publish_response.json()["data"]["task_id"]

    monkeypatch.setattr(
        task_service,
        "_now",
        lambda: datetime(2026, 7, 10, 12, 44, tzinfo=UTC),
    )

    checkin_response = api_client.post(
        f"/api/v1/tasks/{task_id}/checkins",
        headers=auth_headers(member),
        json={"execute_date": "2026-07-02", "is_completed": True},
    )
    assert checkin_response.status_code == 200

    detail_response = api_client.get(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers(member),
    )
    assert detail_response.status_code == 200
    content = detail_response.json()["data"]["activities"][0]["content"]
    assert content == "Nietzsche 于 2026-07-10 完成投喂"


def test_map_init_and_points_use_dynamic_feeding_completion_filters(api_client, db_session):
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session, nickname="Nietzsche")
    campus = seed_campus(db_session)
    payload = publish_payload(campus)
    today = date.today().isoformat()
    payload["execute_dates"] = [today]

    publish_response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(admin),
        json=payload,
    )
    assert publish_response.status_code == 200
    task_id = publish_response.json()["data"]["task_id"]

    init_response = api_client.get("/api/v1/map/init", headers=auth_headers(member))
    assert init_response.status_code == 200
    filter_options = init_response.json()["data"]["filter_options"]
    assert [item["key"] for item in filter_options] == ["none", "feeding_pending"]

    pending_response = api_client.get(
        "/api/v1/map/points?filter_key=feeding_pending",
        headers=auth_headers(member),
    )
    assert pending_response.status_code == 200
    pending_marker = pending_response.json()["data"]["items"][0]
    assert pending_marker["business_id"] == task_id
    assert pending_marker["lng"] == 115.06321
    assert pending_marker["lat"] == 30.23108
    assert pending_marker["cover_photo_url"] == "https://img.example.com/task-feeding-thumb.jpg"
    assert pending_marker["extra"]["location_detail"] == "靠近教学楼B后方草坪"
    assert pending_marker["extra"]["task_status_label"] == "进行中"
    assert pending_marker["extra"]["feeding_status"] == "pending"

    checkin_response = api_client.post(
        f"/api/v1/tasks/{task_id}/checkins",
        headers=auth_headers(member),
        json={"execute_date": today, "is_completed": True},
    )
    assert checkin_response.status_code == 200

    completed_init_response = api_client.get(
        "/api/v1/map/init",
        headers=auth_headers(member),
    )
    completed_filter_options = completed_init_response.json()["data"]["filter_options"]
    assert [item["key"] for item in completed_filter_options] == [
        "none",
        "feeding_completed",
    ]

    completed_response = api_client.get(
        "/api/v1/map/points?filter_key=feeding_completed",
        headers=auth_headers(member),
    )
    assert completed_response.status_code == 200
    completed_marker = completed_response.json()["data"]["items"][0]
    assert completed_marker["business_id"] == task_id
    assert completed_marker["extra"]["feeding_status"] == "completed"
    assert completed_marker["extra"]["task_status_label"] == "已完成"

    second_payload = publish_payload(campus)
    second_payload["title"] = "second feeding task"
    second_payload["execute_dates"] = [today]
    second_payload["map_point"]["lng"] = 115.06421
    second_payload["map_point"]["lat"] = 30.23158
    second_response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(admin),
        json=second_payload,
    )
    assert second_response.status_code == 200

    mixed_init_response = api_client.get("/api/v1/map/init", headers=auth_headers(member))
    assert mixed_init_response.status_code == 200
    mixed_filter_options = mixed_init_response.json()["data"]["filter_options"]
    assert [item["key"] for item in mixed_filter_options] == [
        "none",
        "all",
        "feeding_pending",
        "feeding_completed",
    ]


def test_member_cannot_publish_summer_feeding_task(api_client, db_session):
    member = create_user(db_session)
    campus = seed_campus(db_session)

    response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(member),
        json=publish_payload(campus),
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40302
