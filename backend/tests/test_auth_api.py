from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.modules.auth.captcha import hash_captcha_code
from app.modules.auth.models import AuthCaptcha, User, UserProfile


def create_user(
    db: Session,
    *,
    student_no: str = "20252160A1010",
    password: str = "Password123",
    role: str = "member",
    status: str = "active",
    must_change_password: bool = True,
    profile_completed: bool = False,
) -> User:
    user = User(
        student_no=student_no,
        password_hash=hash_password(password),
        role=role,
        status=status,
        must_change_password=must_change_password,
    )
    db.add(user)
    db.flush()
    db.add(
        UserProfile(
            user_id=user.id,
            nickname="小林",
            real_name="林同学",
            department="计算机学院",
            grade="2025",
            profile_completed=profile_completed,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def create_captcha(db: Session, code: str = "A7KD") -> AuthCaptcha:
    captcha = AuthCaptcha(
        code_hash=hash_captcha_code(code),
        expires_at=datetime.now(tz=UTC) + timedelta(minutes=5),
    )
    db.add(captcha)
    db.commit()
    db.refresh(captcha)
    return captcha


def create_token(user: User) -> str:
    return create_access_token(
        user_id=user.id,
        student_no=user.student_no,
        role=user.role,
        token_version=user.token_version,
    )


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_get_captcha_returns_frontend_contract(api_client):
    response = api_client.get("/api/v1/auth/captcha")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["captcha_id"]
    assert payload["data"]["captcha_image"].startswith("data:image/svg+xml;base64,")
    assert payload["data"]["expires_in"] == 300


def test_login_with_student_number_password_and_captcha(api_client, db_session):
    create_user(db_session)
    captcha = create_captcha(db_session)

    response = api_client.post(
        "/api/v1/auth/login",
        json={
            "student_no": "20252160A1010",
            "password": "Password123",
            "captcha_id": str(captcha.id),
            "captcha_code": "A7KD",
            "agree_terms": True,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 604800
    assert data["must_change_password"] is True
    assert data["next_action"] == "change_password"
    assert data["user"]["meow_no"] == "20252160A1010"
    assert data["user"]["student_no"] == "20252160A1010"
    assert data["user"]["nickname"] == "小林"
    assert data["access_token"]


def test_login_accepts_meow_no_alias_and_routes_to_profile_completion(api_client, db_session):
    create_user(
        db_session,
        student_no="trmx0001",
        password="trmx0001",
        must_change_password=False,
        profile_completed=False,
    )
    captcha = create_captcha(db_session)

    response = api_client.post(
        "/api/v1/auth/login",
        json={
            "meow_no": "trmx0001",
            "password": "trmx0001",
            "captcha_id": str(captcha.id),
            "captcha_code": "A7KD",
            "agree_terms": True,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["next_action"] == "complete_profile"
    assert data["user"]["meow_no"] == "trmx0001"
    assert data["user"]["profile_completed"] is False


def test_login_password_failure_does_not_consume_captcha(api_client, db_session):
    user = create_user(db_session)
    captcha = create_captcha(db_session)

    response = api_client.post(
        "/api/v1/auth/login",
        json={
            "student_no": "20252160A1010",
            "password": "WrongPassword123",
            "captcha_id": str(captcha.id),
            "captcha_code": "A7KD",
            "agree_terms": True,
        },
    )

    assert response.status_code == 401
    db_session.refresh(captcha)
    db_session.refresh(user)
    assert captcha.used_at is None
    assert user.login_failed_count == 1


def test_login_rejects_missing_agreement(api_client, db_session):
    create_user(db_session)
    captcha = create_captcha(db_session)

    response = api_client.post(
        "/api/v1/auth/login",
        json={
            "student_no": "20252160A1010",
            "password": "Password123",
            "captcha_id": str(captcha.id),
            "captcha_code": "A7KD",
            "agree_terms": False,
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40005


def test_get_current_user_returns_profile(api_client, db_session):
    user = create_user(db_session)
    token = create_token(user)

    response = api_client.get("/api/v1/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["meow_no"] == "20252160A1010"
    assert data["student_no"] == "20252160A1010"
    assert data["must_change_password"] is True
    assert data["profile_completed"] is False
    assert data["profile"]["nickname"] == "小林"


def test_renew_access_token_extends_valid_session(api_client, db_session):
    user = create_user(db_session, must_change_password=False)
    token = create_token(user)

    response = api_client.post("/api/v1/auth/renew", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["access_token"] != token
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 604800

    renewed_response = api_client.get("/api/v1/auth/me", headers=auth_headers(data["access_token"]))
    assert renewed_response.status_code == 200
    assert renewed_response.json()["data"]["student_no"] == "20252160A1010"


def test_renew_access_token_requires_password_changed(api_client, db_session):
    user = create_user(db_session, must_change_password=True)
    token = create_token(user)

    response = api_client.post("/api/v1/auth/renew", headers=auth_headers(token))

    assert response.status_code == 403
    assert response.json()["code"] == 40301


def test_change_password_returns_new_token_for_profile_initialization(api_client, db_session):
    user = create_user(db_session)
    token = create_token(user)

    response = api_client.patch(
        "/api/v1/auth/password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "old_password": "Password123",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["token_type"] == "Bearer"
    assert data["must_change_password"] is False
    assert data["profile_completed"] is False
    assert data["next_action"] == "complete_profile"
    db_session.refresh(user)
    assert user.must_change_password is False
    assert user.token_version == 2

    old_token_response = api_client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert old_token_response.status_code == 401

    current_response = api_client.get(
        "/api/v1/auth/me",
        headers=auth_headers(data["access_token"]),
    )
    assert current_response.status_code == 200
    assert current_response.json()["data"]["must_change_password"] is False


def test_change_password_rejects_disallowed_characters(api_client, db_session):
    user = create_user(db_session)
    token = create_token(user)

    response = api_client.patch(
        "/api/v1/auth/password",
        headers=auth_headers(token),
        json={
            "old_password": "Password123",
            "new_password": "NewPassword123#",
            "confirm_password": "NewPassword123#",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40001


def test_logout_requires_valid_token(api_client, db_session):
    user = create_user(db_session)
    token = create_token(user)

    response = api_client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["message"] == "logout success"
    assert response.json()["data"] is None
