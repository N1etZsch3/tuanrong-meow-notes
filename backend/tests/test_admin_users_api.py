from uuid import uuid4

from app.core.errors import ErrorCode
from app.modules.auth.models import AdminOperationLog, User
from tests.test_auth_api import create_captcha, create_token, create_user


def set_profile_department(db_session, user: User, department: str) -> None:
    user.profile.department = department
    db_session.add(user.profile)
    db_session.commit()
    db_session.refresh(user)


def bind_wechat(db_session, user: User, openid: str = "openid-member-1") -> None:
    from datetime import UTC, datetime

    bound_at = datetime.now(tz=UTC)
    user.wechat_openid = openid
    user.wechat_bound_at = bound_at
    user.last_wechat_login_at = bound_at
    db_session.commit()
    db_session.refresh(user)


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
    assert data["meow_no"] == "20252160A1011"
    assert data["must_change_password"] is True
    assert db_session.query(User).filter_by(student_no="20252160A1011").one()


def test_admin_create_member_generates_meow_no_and_uses_it_as_initial_password(
    api_client,
    db_session,
):
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
            "role": "member",
            "profile": {
                "nickname": "新成员",
                "department": "生存保障部",
            },
            "must_change_password": True,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["meow_no"] == "trmx0001"
    assert data["student_no"] == "trmx0001"
    assert data["must_change_password"] is True

    captcha = create_captcha(db_session)
    login_response = api_client.post(
        "/api/v1/auth/login",
        json={
            "meow_no": "trmx0001",
            "password": "trmx0001",
            "captcha_id": str(captcha.id),
            "captcha_code": "A7KD",
            "agree_terms": True,
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["data"]["next_action"] == "change_password"


def test_manual_high_meow_no_does_not_advance_automatic_sequence(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin001",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    for sequence in range(1, 10):
        create_user(
            db_session,
            student_no=f"trmx{sequence:04d}",
            must_change_password=False,
        )
    token = create_token(admin)

    manual_response = api_client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"meow_no": "trmx2313", "role": "member"},
    )
    assert manual_response.status_code == 200
    assert manual_response.json()["data"]["meow_no"] == "trmx2313"

    automatic_response = api_client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "member"},
    )
    assert automatic_response.status_code == 200
    assert automatic_response.json()["data"]["meow_no"] == "trmx0010"


def test_admin_create_member_without_initial_profile_leaves_fields_empty(api_client, db_session):
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
        json={"role": "member", "must_change_password": True},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    user = db_session.query(User).filter_by(student_no=data["meow_no"]).one()
    assert user.profile.nickname == ""
    assert user.profile.real_name is None
    assert user.profile.department is None


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


def test_admin_can_create_summer_volunteer_with_member_permissions(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin002",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    token = create_token(admin)

    response = api_client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_no": "trmx2026",
            "initial_password": "Password123",
            "role": "summer_volunteer",
            "profile": {"nickname": "summer helper"},
            "must_change_password": False,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["role"] == "summer_volunteer"

    volunteer = db_session.query(User).filter_by(student_no="trmx2026").one()
    volunteer_token = create_token(volunteer)
    forbidden_response = api_client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {volunteer_token}"},
        json={
            "student_no": "trmx2027",
            "initial_password": "Password123",
            "profile": {"nickname": "not allowed"},
        },
    )

    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["code"] == 40302


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


def test_admin_user_list_filters_by_department_and_sorts_by_meow_no(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin001",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    first = create_user(
        db_session,
        student_no="trmx0003",
        must_change_password=False,
    )
    second = create_user(
        db_session,
        student_no="trmx0001",
        role="summer_volunteer",
        must_change_password=False,
    )
    third = create_user(
        db_session,
        student_no="trmx0002",
        must_change_password=False,
    )
    set_profile_department(db_session, first, "活动部")
    set_profile_department(db_session, second, "生存保障部")
    set_profile_department(db_session, third, "活动部")
    token = create_token(admin)

    asc_response = api_client.get(
        "/api/v1/admin/users?department=活动部&sort_by=meow_no&sort_order=asc&page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert asc_response.status_code == 200
    asc_items = asc_response.json()["data"]["items"]
    assert [item["meow_no"] for item in asc_items] == ["trmx0002", "trmx0003"]

    desc_response = api_client.get(
        "/api/v1/admin/users?department=活动部&sort_by=meow_no&sort_order=desc&page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert desc_response.status_code == 200
    desc_items = desc_response.json()["data"]["items"]
    assert [item["meow_no"] for item in desc_items] == ["trmx0003", "trmx0002"]


def test_admin_can_view_and_update_non_admin_member_detail(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin001",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    member = create_user(
        db_session,
        student_no="trmx0101",
        must_change_password=False,
    )
    bind_wechat(db_session, member, openid="openid-detail-member")
    token = create_token(admin)

    detail_response = api_client.get(
        f"/api/v1/admin/users/{member.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["meow_no"] == "trmx0101"
    assert detail["editable"] is True
    assert detail["can_reset_password"] is True
    assert detail["wechat_bound"] is True

    update_response = api_client.patch(
        f"/api/v1/admin/users/{member.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "role": "summer_volunteer",
            "status": "active",
            "profile": {
                "nickname": "新昵称",
                "real_name": "新姓名",
                "department": "宣传部",
                "grade": "2026",
                "contact_info": "wx-cat-helper",
            },
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["meow_no"] == "trmx0101"
    assert updated["role"] == "summer_volunteer"
    assert updated["profile"]["nickname"] == "新昵称"
    assert updated["profile"]["department"] == "宣传部"
    assert updated["profile"]["contact_info"] == "wx-cat-helper"


def test_admin_can_update_member_after_avatar_review_adds_nested_uuid(
    api_client,
    db_session,
):
    admin = create_user(
        db_session,
        student_no="admin-avatar-log",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    member = create_user(
        db_session,
        student_no="trmx-avatar-log",
        must_change_password=False,
    )
    review_asset_id = uuid4()
    member.profile.avatar_review_asset_id = review_asset_id
    member.profile.avatar_review_status = "passed"
    db_session.commit()
    token = create_token(admin)

    response = api_client.patch(
        f"/api/v1/admin/users/{member.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "role": "member",
            "status": "active",
            "profile": {
                "nickname": "微信审核账号",
                "real_name": None,
                "department": "审核专用",
                "grade": None,
                "contact_info": None,
            },
        },
    )

    assert response.status_code == 200
    operation = (
        db_session.query(AdminOperationLog)
        .filter(AdminOperationLog.operation_type == "user_update_detail")
        .one()
    )
    assert operation.before_data["profile"]["avatar_review_asset_id"] == str(
        review_asset_id
    )


def test_admin_cannot_bypass_avatar_review_with_direct_url(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin-avatar-security",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    member = create_user(
        db_session,
        student_no="trmx-avatar-security",
        must_change_password=False,
    )
    token = create_token(admin)

    response = api_client.patch(
        f"/api/v1/admin/users/{member.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "profile": {
                "nickname": member.profile.nickname,
                "avatar_url": "https://unreviewed.example/avatar.jpg",
            }
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == int(ErrorCode.FILE_SECURITY_REJECTED)


def test_admin_can_soft_delete_non_admin_member(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin001",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    member = create_user(
        db_session,
        student_no="trmx0201",
        must_change_password=False,
    )
    token = create_token(admin)
    original_token_version = member.token_version

    response = api_client.delete(
        f"/api/v1/admin/users/{member.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user_id"] == str(member.id)
    assert data["status"] == "left"
    assert data["deleted_at"]

    db_session.refresh(member)
    assert member.status == "left"
    assert member.deleted_at is not None
    assert member.token_version == original_token_version + 1

    list_response = api_client.get(
        "/api/v1/admin/users?page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert all(item["id"] != str(member.id) for item in list_data["items"])

    detail_response = api_client.get(
        f"/api/v1/admin/users/{member.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_response.status_code == 404


def test_admin_can_clear_member_wechat_binding_and_invalidate_token(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin001",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    member = create_user(
        db_session,
        student_no="trmx0301",
        must_change_password=False,
        profile_completed=True,
    )
    bind_wechat(db_session, member)
    member_token = create_token(member)
    admin_token = create_token(admin)
    original_token_version = member.token_version

    response = api_client.delete(
        f"/api/v1/admin/users/{member.id}/wechat-binding",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "user_id": str(member.id),
        "wechat_bound": False,
        "token_version": original_token_version + 1,
    }
    db_session.refresh(member)
    assert member.wechat_openid is None
    assert member.wechat_bound_at is None
    assert member.last_wechat_login_at is None
    assert member.token_version == original_token_version + 1

    old_token_response = api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert old_token_response.status_code == 401


def test_member_cannot_clear_wechat_binding(api_client, db_session):
    actor = create_user(
        db_session,
        student_no="trmx0300",
        must_change_password=False,
    )
    target = create_user(
        db_session,
        student_no="trmx0301",
        must_change_password=False,
    )
    bind_wechat(db_session, target)
    token = create_token(actor)

    response = api_client.delete(
        f"/api/v1/admin/users/{target.id}/wechat-binding",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40302


def test_admin_cannot_clear_admin_wechat_binding(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin001",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    target_admin = create_user(
        db_session,
        student_no="admin002",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    bind_wechat(db_session, target_admin)
    token = create_token(admin)

    response = api_client.delete(
        f"/api/v1/admin/users/{target_admin.id}/wechat-binding",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_cannot_modify_or_reset_admin_account(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="admin001",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    target_admin = create_user(
        db_session,
        student_no="admin002",
        password="AdminPassword123",
        role="admin",
        must_change_password=False,
    )
    token = create_token(admin)

    detail_response = api_client.get(
        f"/api/v1/admin/users/{target_admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["editable"] is False
    assert detail["can_reset_password"] is False

    update_response = api_client.patch(
        f"/api/v1/admin/users/{target_admin.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"profile": {"nickname": "不能修改"}},
    )
    assert update_response.status_code == 403

    reset_response = api_client.patch(
        f"/api/v1/admin/users/{target_admin.id}/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"new_password": "ResetPassword123", "must_change_password": True},
    )
    assert reset_response.status_code == 403

    delete_response = api_client.delete(
        f"/api/v1/admin/users/{target_admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 403
    db_session.refresh(target_admin)
    assert target_admin.deleted_at is None
