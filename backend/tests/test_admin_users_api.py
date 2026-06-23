from app.modules.auth.models import User
from tests.test_auth_api import create_token, create_user


def test_admin_can_create_member_account(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin001",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    token = create_token(admin)

    response = api_client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_no": "20252160A1011",
            "initial_password": "Password123",
            "role": "member",
            "profile": {
                "nickname": "小橘",
                "real_name": "橘同学",
                "department": "动物保护协会",
                "grade": "2025",
            },
            "must_change_password": True,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["student_no"] == "20252160A1011"
    assert data["must_change_password"] is True
    assert db_session.query(User).filter_by(student_no="20252160A1011").one()


def test_member_cannot_create_member_account(api_client, db_session):
    member = create_user(db_session, must_change_password=False)
    token = create_token(member)

    response = api_client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_no": "20252160A1011",
            "initial_password": "Password123",
            "profile": {"nickname": "小橘"},
        },
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40302


def test_admin_can_list_reset_status_and_role(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin001",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    member = create_user(db_session, student_no="20252160A1011", must_change_password=False)
    token = create_token(admin)

    list_response = api_client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 2

    reset_response = api_client.patch(
        f"/api/v1/admin/users/{member.id}/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"new_password": "ResetPassword123", "must_change_password": True},
    )
    assert reset_response.status_code == 200
    db_session.refresh(member)
    assert member.must_change_password is True
    assert member.token_version == 2

    status_response = api_client.patch(
        f"/api/v1/admin/users/{member.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "blocked", "reason": "已退出猫协"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["data"]["status"] == "blocked"

    role_response = api_client.patch(
        f"/api/v1/admin/users/{member.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin"},
    )
    assert role_response.status_code == 200
    assert role_response.json()["data"]["role"] == "admin"
