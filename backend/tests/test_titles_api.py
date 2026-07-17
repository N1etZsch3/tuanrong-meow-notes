from app.modules.auth.models import AdminOperationLog, User
from tests.test_auth_api import auth_headers, create_token, create_user


def assign_title(db_session, user: User, title: str) -> None:
    user.profile.title = title
    db_session.commit()
    db_session.refresh(user)


def create_president(db_session, *, student_no: str = "trmx7199") -> User:
    user = create_user(
        db_session,
        student_no=student_no,
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    assign_title(db_session, user, "president")
    return user


def assert_vice_president_payload(payload: dict) -> None:
    assert payload["title"] == "vice_president"
    assert payload["title_label"] == "副会长"
    assert payload["title_shield"] == "purple"


def test_title_fields_are_exposed_by_current_profile_dashboard_and_admin_payloads(
    api_client,
    db_session,
):
    member = create_user(
        db_session,
        student_no="trmx7101",
        must_change_password=False,
        profile_completed=True,
    )
    assign_title(db_session, member, "vice_president")
    member_headers = auth_headers(create_token(member))

    auth_response = api_client.get("/api/v1/auth/me", headers=member_headers)
    assert auth_response.status_code == 200
    assert_vice_president_payload(auth_response.json()["data"]["profile"])

    profile_response = api_client.get("/api/v1/profile/me", headers=member_headers)
    assert profile_response.status_code == 200
    assert_vice_president_payload(profile_response.json()["data"])

    dashboard_response = api_client.get("/api/v1/me/dashboard", headers=member_headers)
    assert dashboard_response.status_code == 200
    assert_vice_president_payload(dashboard_response.json()["data"]["profile"])

    admin = create_user(
        db_session,
        student_no="trmx7102",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    admin_response = api_client.get(
        f"/api/v1/admin/users/{member.id}",
        headers=auth_headers(create_token(admin)),
    )
    assert admin_response.status_code == 200
    assert_vice_president_payload(admin_response.json()["data"]["profile"])


def test_president_can_list_all_title_slots_with_current_holders(api_client, db_session):
    president = create_user(
        db_session,
        student_no="trmx7111",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    assign_title(db_session, president, "president")
    vice_president = create_user(
        db_session,
        student_no="trmx7112",
        must_change_password=False,
        profile_completed=True,
    )
    assign_title(db_session, vice_president, "vice_president")

    response = api_client.get(
        "/api/v1/admin/titles",
        headers=auth_headers(create_token(president)),
    )

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 12
    assert [item["key"] for item in items[:2]] == ["president", "vice_president"]
    vice_item = next(item for item in items if item["key"] == "vice_president")
    assert vice_item == {
        "key": "vice_president",
        "label": "副会长",
        "shield": "purple",
        "is_available": False,
        "holder": {
            "user_id": str(vice_president.id),
            "meow_no": "trmx7112",
            "nickname": "小林",
        },
    }
    empty_item = next(item for item in items if item["key"] == "survival_head")
    assert empty_item["is_available"] is True
    assert empty_item["holder"] is None


def test_regular_admin_cannot_list_title_slots(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="trmx7113",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )

    response = api_client.get(
        "/api/v1/admin/titles",
        headers=auth_headers(create_token(admin)),
    )

    assert response.status_code == 403
    assert response.json()["code"] == 63010


def test_president_can_grant_and_revoke_an_available_title(api_client, db_session):
    president = create_president(db_session)
    member = create_user(
        db_session,
        student_no="trmx7121",
        must_change_password=False,
        profile_completed=True,
    )
    headers = auth_headers(create_token(president))

    grant_response = api_client.patch(
        f"/api/v1/admin/users/{member.id}/title",
        headers=headers,
        json={"title": "publicity_head"},
    )

    assert grant_response.status_code == 200
    assert grant_response.json()["data"]["profile"]["title"] == "publicity_head"
    db_session.refresh(member.profile)
    assert member.profile.title == "publicity_head"

    revoke_response = api_client.patch(
        f"/api/v1/admin/users/{member.id}/title",
        headers=headers,
        json={"title": "none"},
    )

    assert revoke_response.status_code == 200
    assert revoke_response.json()["data"]["profile"]["title"] is None
    db_session.refresh(member.profile)
    assert member.profile.title is None
    logs = db_session.query(AdminOperationLog).filter_by(operation_type="user_title_update").all()
    assert len(logs) == 2


def test_granting_an_occupied_title_returns_conflict_without_changes(api_client, db_session):
    president = create_president(db_session)
    holder = create_user(
        db_session,
        student_no="trmx7122",
        must_change_password=False,
        profile_completed=True,
    )
    assign_title(db_session, holder, "activity_head")
    target = create_user(
        db_session,
        student_no="trmx7123",
        must_change_password=False,
        profile_completed=True,
    )

    response = api_client.patch(
        f"/api/v1/admin/users/{target.id}/title",
        headers=auth_headers(create_token(president)),
        json={"title": "activity_head"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == 63009
    db_session.refresh(holder.profile)
    db_session.refresh(target.profile)
    assert holder.profile.title == "activity_head"
    assert target.profile.title is None


def test_regular_admin_cannot_grant_titles(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="trmx7124",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    member = create_user(
        db_session,
        student_no="trmx7125",
        must_change_password=False,
        profile_completed=True,
    )

    response = api_client.patch(
        f"/api/v1/admin/users/{member.id}/title",
        headers=auth_headers(create_token(admin)),
        json={"title": "care_head"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == 63010


def test_president_title_cannot_flow_through_the_regular_grant_endpoint(api_client, db_session):
    president = create_president(db_session)
    member = create_user(
        db_session,
        student_no="trmx7126",
        must_change_password=False,
        profile_completed=True,
    )

    response = api_client.patch(
        f"/api/v1/admin/users/{member.id}/title",
        headers=auth_headers(create_token(president)),
        json={"title": "president"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == 63011


def test_only_president_can_create_a_member_with_an_initial_title(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="trmx7127",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    rejected = api_client.post(
        "/api/v1/admin/users",
        headers=auth_headers(create_token(admin)),
        json={
            "meow_no": "trmx7128",
            "initial_password": "Password123",
            "profile": {"nickname": "新成员", "title": "secretary_head"},
        },
    )
    assert rejected.status_code == 403
    assert rejected.json()["code"] == 63010

    president = create_president(db_session, student_no="trmx7129")
    created = api_client.post(
        "/api/v1/admin/users",
        headers=auth_headers(create_token(president)),
        json={
            "meow_no": "trmx7130",
            "initial_password": "Password123",
            "profile": {"nickname": "新成员", "title": "secretary_head"},
        },
    )
    assert created.status_code == 200
    new_user = db_session.query(User).filter_by(student_no="trmx7130").one()
    assert new_user.profile.title == "secretary_head"
