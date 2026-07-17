from uuid import uuid4

from app.modules.notifications.dispatch import create_notifications
from app.modules.notifications.models import Notification, UserNotificationSetting
from tests.test_auth_api import auth_headers, create_token, create_user


def seed_notification(db_session, user, **overrides):
    payload = {
        "user_id": user.id,
        "notification_type": "new_task",
        "title": "新任务已发布",
        "content": "白敬亭喂食任务已发布",
        "related_type": "task",
        "related_id": uuid4(),
        "is_read": False,
    }
    payload.update(overrides)
    notification = Notification(**payload)
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


def test_notification_list_paginates_and_filters(api_client, db_session):
    user = create_user(db_session, student_no="trmx0100", must_change_password=False)
    other = create_user(db_session, student_no="trmx0101", must_change_password=False)
    for index in range(12):
        seed_notification(db_session, user, title=f"通知{index}", is_read=index < 2)
    seed_notification(db_session, other, title="他人的通知")
    token = create_token(user)

    response = api_client.get(
        "/api/v1/me/notifications?page=1&page_size=10",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 12
    assert data["page_size"] == 10
    assert data["has_more"] is True
    assert len(data["items"]) == 10
    item = data["items"][0]
    for field in (
        "id",
        "notification_type",
        "title",
        "content",
        "related_type",
        "related_id",
        "is_read",
        "read_at",
        "created_at",
    ):
        assert field in item

    unread_only = api_client.get(
        "/api/v1/me/notifications?is_read=false&page_size=100",
        headers=auth_headers(token),
    )
    assert unread_only.status_code == 200
    assert unread_only.json()["data"]["total"] == 10

    typed = api_client.get(
        "/api/v1/me/notifications?notification_type=announcement",
        headers=auth_headers(token),
    )
    assert typed.status_code == 200
    assert typed.json()["data"]["total"] == 0


def test_notification_unread_count_and_read_flow(api_client, db_session):
    user = create_user(db_session, student_no="trmx0102", must_change_password=False)
    first = seed_notification(db_session, user)
    seed_notification(db_session, user, title="第二条")
    token = create_token(user)

    count = api_client.get(
        "/api/v1/me/notifications/unread-count", headers=auth_headers(token)
    )
    assert count.status_code == 200
    assert count.json()["data"]["unread_count"] == 2

    read_one = api_client.patch(
        f"/api/v1/me/notifications/{first.id}/read", headers=auth_headers(token)
    )
    assert read_one.status_code == 200
    read_data = read_one.json()["data"]
    assert read_data["is_read"] is True
    assert read_data["read_at"] is not None

    read_all = api_client.patch(
        "/api/v1/me/notifications/read-all", headers=auth_headers(token)
    )
    assert read_all.status_code == 200
    assert read_all.json()["data"]["updated_count"] == 1

    count_after = api_client.get(
        "/api/v1/me/notifications/unread-count", headers=auth_headers(token)
    )
    assert count_after.json()["data"]["unread_count"] == 0


def test_notification_read_rejects_missing_and_foreign(api_client, db_session):
    user = create_user(db_session, student_no="trmx0103", must_change_password=False)
    other = create_user(db_session, student_no="trmx0104", must_change_password=False)
    foreign = seed_notification(db_session, other)
    token = create_token(user)

    missing = api_client.patch(
        f"/api/v1/me/notifications/{uuid4()}/read", headers=auth_headers(token)
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == 63007

    forbidden = api_client.patch(
        f"/api/v1/me/notifications/{foreign.id}/read", headers=auth_headers(token)
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == 63008


def test_notification_settings_default_open_and_update(api_client, db_session):
    user = create_user(db_session, student_no="trmx0105", must_change_password=False)
    token = create_token(user)

    initial = api_client.get(
        "/api/v1/me/notification-settings", headers=auth_headers(token)
    )
    assert initial.status_code == 200
    settings = initial.json()["data"]
    assert settings == {
        "task_enabled": True,
        "feeding_enabled": True,
        "medicine_enabled": True,
        "supply_enabled": True,
        "member_enabled": True,
        "cat_enabled": True,
        "announcement_enabled": True,
    }

    updated = api_client.patch(
        "/api/v1/me/notification-settings",
        headers=auth_headers(token),
        json={"task_enabled": False, "cat_enabled": False},
    )
    assert updated.status_code == 200
    updated_data = updated.json()["data"]
    assert updated_data["task_enabled"] is False
    assert updated_data["cat_enabled"] is False
    assert updated_data["supply_enabled"] is True


def test_dispatch_respects_channel_switches(db_session):
    receiver = create_user(db_session, student_no="trmx0106", must_change_password=False)
    muted = create_user(db_session, student_no="trmx0107", must_change_password=False)
    db_session.add(
        UserNotificationSetting(user_id=muted.id, task_enabled=False)
    )
    db_session.commit()

    created = create_notifications(
        db_session,
        user_ids=[receiver.id, muted.id],
        notification_type="new_task",
        title="新任务已发布",
    )
    db_session.commit()

    assert [item.user_id for item in created] == [receiver.id]


def test_publish_summer_feeding_task_notifies_active_members(api_client, db_session):
    from tests.test_tasks_api import publish_payload, seed_campus

    admin = create_user(
        db_session,
        student_no="admin080",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    member = create_user(db_session, student_no="trmx0108", must_change_password=False)
    blocked = create_user(
        db_session, student_no="trmx0109", must_change_password=False, status="blocked"
    )
    campus = seed_campus(db_session)
    token = create_token(admin)

    response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(token),
        json=publish_payload(campus),
    )
    assert response.status_code == 200

    member_rows = db_session.query(Notification).filter_by(user_id=member.id).all()
    assert len(member_rows) == 1
    assert member_rows[0].notification_type == "new_task"
    assert member_rows[0].related_type == "task"
    assert db_session.query(Notification).filter_by(user_id=admin.id).count() == 0
    assert db_session.query(Notification).filter_by(user_id=blocked.id).count() == 0


def test_dashboard_todo_reports_real_unread_count(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0110",
        must_change_password=False,
        profile_completed=True,
    )
    seed_notification(db_session, user)
    token = create_token(user)

    response = api_client.get("/api/v1/me/dashboard", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["data"]["todo"]["unread_notifications"] == 1


def test_websocket_rejects_bad_token_and_accepts_valid(api_client, db_session):
    user = create_user(db_session, student_no="trmx0111", must_change_password=False)
    token = create_token(user)

    # 坏 token：连接直接被关闭
    try:
        with api_client.websocket_connect("/api/v1/ws/notifications?token=bad-token") as ws:
            ws.receive_text()
        raised = False
    except Exception:
        raised = True
    assert raised

    # 好 token：可连接并 ping/pong
    with api_client.websocket_connect(
        f"/api/v1/ws/notifications?token={token}"
    ) as ws:
        ws.send_text('{"type": "ping"}')
        reply = ws.receive_json()
        assert reply == {"type": "pong"}
