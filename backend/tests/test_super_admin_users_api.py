from uuid import UUID

from app.core.security import verify_password
from app.modules.auth.models import AdminOperationLog
from app.modules.titles.service import seed_president
from tests.test_auth_api import auth_headers, create_token, create_user


def create_super_admin(db_session, *, student_no: str = "trmx9000"):
    user = create_user(
        db_session,
        student_no=student_no,
        must_change_password=False,
        profile_completed=True,
    )
    return seed_president(db_session, user=user)


def test_regular_admin_cannot_create_or_assign_an_admin(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="trmx9001",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    member = create_user(
        db_session,
        student_no="trmx9002",
        must_change_password=False,
        profile_completed=True,
    )
    headers = auth_headers(create_token(admin))

    created = api_client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "meow_no": "trmx9003",
            "initial_password": "Password123",
            "role": "admin",
            "profile": {"nickname": "越权管理员"},
        },
    )
    assert created.status_code == 400

    promoted = api_client.patch(
        f"/api/v1/admin/users/{member.id}/role",
        headers=headers,
        json={"role": "admin"},
    )
    assert promoted.status_code == 400
    db_session.refresh(member)
    assert member.role == "member"


def test_super_admin_uses_dedicated_api_to_create_and_manage_admins(api_client, db_session):
    super_admin = create_super_admin(db_session)
    headers = auth_headers(create_token(super_admin))

    created = api_client.post(
        "/api/v1/super-admin/users/admins",
        headers=headers,
        json={
            "meow_no": "trmx9004",
            "initial_password": "Password123",
            "role": "admin",
            "profile": {"nickname": "新管理员", "departments": ["宣传部"]},
        },
    )
    assert created.status_code == 200
    target_id = created.json()["data"]["id"]

    detail = api_client.get(
        f"/api/v1/admin/users/{target_id}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["editable"] is True
    assert detail.json()["data"]["can_reset_password"] is True

    standard_update = api_client.patch(
        f"/api/v1/admin/users/{target_id}",
        headers=headers,
        json={"profile": {"nickname": "错误入口"}},
    )
    assert standard_update.status_code == 403

    updated = api_client.patch(
        f"/api/v1/super-admin/users/{target_id}",
        headers=headers,
        json={"profile": {"nickname": "已修改管理员", "departments": ["秘书部"]}},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["profile"]["nickname"] == "已修改管理员"

    reset = api_client.patch(
        f"/api/v1/super-admin/users/{target_id}/reset-password",
        headers=headers,
        json={"new_password": "ResetPassword123", "must_change_password": True},
    )
    assert reset.status_code == 200

    target = db_session.get(type(super_admin), UUID(target_id))
    assert target is not None
    assert verify_password("ResetPassword123", target.password_hash)
    assert (
        db_session.query(AdminOperationLog)
        .filter_by(operation_type="user_update_detail", target_id=target.id)
        .count()
        == 1
    )


def test_super_admin_can_promote_and_demote_an_admin_but_not_self(api_client, db_session):
    super_admin = create_super_admin(db_session, student_no="trmx9010")
    member = create_user(
        db_session,
        student_no="trmx9011",
        must_change_password=False,
        profile_completed=True,
    )
    headers = auth_headers(create_token(super_admin))

    promoted = api_client.patch(
        f"/api/v1/super-admin/users/{member.id}/role",
        headers=headers,
        json={"role": "admin"},
    )
    assert promoted.status_code == 200
    db_session.refresh(member)
    assert member.role == "admin"

    demoted = api_client.patch(
        f"/api/v1/super-admin/users/{member.id}/role",
        headers=headers,
        json={"role": "member"},
    )
    assert demoted.status_code == 200
    db_session.refresh(member)
    assert member.role == "member"

    self_update = api_client.patch(
        f"/api/v1/super-admin/users/{super_admin.id}/role",
        headers=headers,
        json={"role": "admin"},
    )
    assert self_update.status_code == 403


def test_president_title_without_super_admin_role_does_not_grant_super_api(
    api_client,
    db_session,
):
    inconsistent = create_user(
        db_session,
        student_no="trmx9020",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    inconsistent.profile.title = "president"
    db_session.commit()

    response = api_client.post(
        "/api/v1/super-admin/users/admins",
        headers=auth_headers(create_token(inconsistent)),
        json={
            "meow_no": "trmx9021",
            "initial_password": "Password123",
            "role": "admin",
        },
    )
    assert response.status_code == 403
