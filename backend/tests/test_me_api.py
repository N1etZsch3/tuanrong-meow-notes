from app.modules.auth.models import UserDepartment
from tests.test_auth_api import auth_headers, create_token, create_user


def test_me_dashboard_returns_profile_stats_and_admin_entry(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="Password123",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    user.profile.nickname = "Nietzsche"
    user.profile.department = "宣传部"
    user.profile.contact_info = "13800138000"
    db_session.add(
        UserDepartment(user_id=user.id, department="宣传部", sort_order=0)
    )
    db_session.commit()
    token = create_token(user)

    response = api_client.get("/api/v1/me/dashboard", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["profile"] == {
        "user_id": str(user.id),
        "student_no": "trmx0001",
        "meow_no": "trmx0001",
        "nickname": "Nietzsche",
        "avatar_url": None,
        "department": "宣传部",
        "departments": ["宣传部"],
            "role": "admin",
            "show_admin_entry": True,
            "title": None,
            "title_label": None,
            "title_shield": None,
        }
    assert data["stats"] == {
        "total_completed_tasks": 0,
        "monthly_completed_tasks": 0,
        "current_in_progress_tasks": 0,
        "total_observation_records": 0,
        "favorite_cats": 0,
    }
    assert data["todo"]["unread_notifications"] == 0
    assert data["recent_tasks"] == []
    assert data["recent_notifications"] == []


def test_me_record_endpoints_return_empty_paginated_contracts(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)

    for path in (
        "/api/v1/me/tasks",
        "/api/v1/me/checkins",
        "/api/v1/me/observations",
        "/api/v1/me/favorite-cats",
    ):
        response = api_client.get(path, headers=auth_headers(token))

        assert response.status_code == 200
        assert response.json()["data"] == {
            "items": [],
            "page": 1,
            "page_size": 20,
            "total": 0,
            "has_more": False,
        }


def test_me_endpoints_require_profile_completed(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="Password123",
        must_change_password=False,
        profile_completed=False,
    )
    token = create_token(user)

    response = api_client.get("/api/v1/me/dashboard", headers=auth_headers(token))

    assert response.status_code == 403
    assert response.json()["code"] == 63006


def test_me_endpoints_require_password_changed(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="Password123",
        must_change_password=True,
        profile_completed=True,
    )
    token = create_token(user)

    response = api_client.get("/api/v1/me/dashboard", headers=auth_headers(token))

    assert response.status_code == 403
    assert response.json()["code"] == 40301
