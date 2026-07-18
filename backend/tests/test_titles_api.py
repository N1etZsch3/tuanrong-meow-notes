import pytest

from app.core.errors import APIError
from app.modules.auth.models import AdminOperationLog, User
from app.modules.titles.service import seed_president
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


def test_member_can_resign_a_non_president_title(api_client, db_session):
    member = create_user(
        db_session,
        student_no="trmx7131",
        must_change_password=False,
        profile_completed=True,
    )
    assign_title(db_session, member, "care_deputy")

    response = api_client.post(
        "/api/v1/profile/me/title/resign",
        headers=auth_headers(create_token(member)),
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "title": None,
        "title_label": None,
        "title_shield": None,
    }
    db_session.refresh(member.profile)
    assert member.profile.title is None
    log = db_session.query(AdminOperationLog).filter_by(operation_type="user_title_resign").one()
    assert log.admin_id == member.id


def test_resigning_without_a_title_is_idempotent(api_client, db_session):
    member = create_user(
        db_session,
        student_no="trmx7132",
        must_change_password=False,
        profile_completed=True,
    )

    response = api_client.post(
        "/api/v1/profile/me/title/resign",
        headers=auth_headers(create_token(member)),
    )

    assert response.status_code == 200
    assert response.json()["data"]["title"] is None
    assert (
        db_session.query(AdminOperationLog).filter_by(operation_type="user_title_resign").count()
        == 0
    )


def test_president_cannot_resign_without_transferring(api_client, db_session):
    president = create_president(db_session, student_no="trmx7133")

    response = api_client.post(
        "/api/v1/profile/me/title/resign",
        headers=auth_headers(create_token(president)),
    )

    assert response.status_code == 403
    assert response.json()["code"] == 63012
    db_session.refresh(president.profile)
    assert president.profile.title == "president"


def test_president_transfer_is_atomic_and_promotes_a_member(api_client, db_session):
    president = create_president(db_session, student_no="trmx7134")
    successor = create_user(
        db_session,
        student_no="trmx7135",
        must_change_password=False,
        profile_completed=True,
    )
    assign_title(db_session, successor, "secretary_deputy")
    previous_token_version = successor.token_version

    response = api_client.post(
        "/api/v1/admin/titles/transfer",
        headers=auth_headers(create_token(president)),
        json={"successor_id": str(successor.id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["previous_president"]["id"] == str(president.id)
    assert data["previous_president"]["profile"]["title"] is None
    assert data["successor"]["id"] == str(successor.id)
    assert data["successor"]["profile"]["title"] == "president"
    db_session.refresh(president)
    db_session.refresh(successor)
    db_session.refresh(president.profile)
    db_session.refresh(successor.profile)
    assert president.profile.title is None
    assert successor.profile.title == "president"
    assert successor.role == "admin"
    assert successor.token_version == previous_token_version + 1
    assert (
        db_session.query(AdminOperationLog).filter_by(operation_type="president_transfer").count()
        == 1
    )


def test_president_transfer_keeps_existing_admin_token_version(api_client, db_session):
    president = create_president(db_session, student_no="trmx7136")
    successor = create_user(
        db_session,
        student_no="trmx7137",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    previous_token_version = successor.token_version

    response = api_client.post(
        "/api/v1/admin/titles/transfer",
        headers=auth_headers(create_token(president)),
        json={"successor_id": str(successor.id)},
    )

    assert response.status_code == 200
    db_session.refresh(successor)
    assert successor.token_version == previous_token_version


def test_president_transfer_rejects_self_and_non_president_actor(api_client, db_session):
    president = create_president(db_session, student_no="trmx7138")
    self_response = api_client.post(
        "/api/v1/admin/titles/transfer",
        headers=auth_headers(create_token(president)),
        json={"successor_id": str(president.id)},
    )
    assert self_response.status_code == 422
    assert self_response.json()["code"] == 63011

    admin = create_user(
        db_session,
        student_no="trmx7139",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    target = create_user(
        db_session,
        student_no="trmx7140",
        must_change_password=False,
        profile_completed=True,
    )
    rejected = api_client.post(
        "/api/v1/admin/titles/transfer",
        headers=auth_headers(create_token(admin)),
        json={"successor_id": str(target.id)},
    )
    assert rejected.status_code == 403
    assert rejected.json()["code"] == 63010


def test_soft_deleting_a_titled_member_releases_the_title(api_client, db_session):
    admin = create_user(
        db_session,
        student_no="trmx7141",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    member = create_user(
        db_session,
        student_no="trmx7142",
        must_change_password=False,
        profile_completed=True,
    )
    assign_title(db_session, member, "activity_deputy")

    response = api_client.delete(
        f"/api/v1/admin/users/{member.id}",
        headers=auth_headers(create_token(admin)),
    )

    assert response.status_code == 200
    db_session.refresh(member.profile)
    assert member.profile.title is None


def test_seed_president_promotes_user_and_rejects_a_second_president(db_session):
    first = create_user(
        db_session,
        student_no="trmx7143",
        must_change_password=False,
        profile_completed=True,
    )
    previous_token_version = first.token_version

    seeded = seed_president(db_session, user=first)

    assert seeded.profile.title == "president"
    assert seeded.role == "admin"
    assert seeded.token_version == previous_token_version + 1

    second = create_user(
        db_session,
        student_no="trmx7144",
        must_change_password=False,
        profile_completed=True,
    )
    with pytest.raises(APIError) as exc_info:
        seed_president(db_session, user=second)
    assert exc_info.value.status_code == 409
    assert exc_info.value.code == 63009
    db_session.refresh(second.profile)
    assert second.profile.title is None
