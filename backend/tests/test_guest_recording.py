from app.modules.auth import service
from app.modules.public.guest_service import record_guest_visit
from app.modules.public.models import WechatGuest
from tests.test_auth_api import create_user, set_wechat_auth_mode


def test_record_guest_visit_inserts_new_guest(db_session):
    record_guest_visit(db_session, "openid-guest-1")

    guest = (
        db_session.query(WechatGuest).filter(WechatGuest.openid == "openid-guest-1").one()
    )
    assert guest.visit_count == 1
    assert guest.first_visit_at is not None
    assert guest.last_visit_at is not None


def test_record_guest_visit_increments_on_repeat(db_session):
    record_guest_visit(db_session, "openid-guest-2")
    first = (
        db_session.query(WechatGuest).filter(WechatGuest.openid == "openid-guest-2").one()
    )
    first_seen = first.first_visit_at

    record_guest_visit(db_session, "openid-guest-2")

    guest = (
        db_session.query(WechatGuest).filter(WechatGuest.openid == "openid-guest-2").one()
    )
    assert guest.visit_count == 2
    assert guest.first_visit_at == first_seen


def test_record_guest_visit_ignores_empty_openid(db_session):
    record_guest_visit(db_session, "")
    assert db_session.query(WechatGuest).count() == 0


def test_record_guest_visit_swallows_errors(monkeypatch):
    class ExplodingSession:
        def scalar(self, *args, **kwargs):
            raise RuntimeError("db down")

        def rollback(self):
            pass

    # Must not raise even if the session misbehaves.
    record_guest_visit(ExplodingSession(), "openid-guest-err")


def test_wechat_unbound_login_records_guest(api_client, db_session, monkeypatch):
    set_wechat_auth_mode(monkeypatch, "optional")
    monkeypatch.setattr(
        service,
        "exchange_wechat_code_for_openid",
        lambda code: "openid-guest-flow",
        raising=False,
    )

    response = api_client.post("/api/v1/auth/wechat/login", json={"code": "code-1"})

    assert response.status_code == 401
    assert response.json()["code"] == 40104

    guest = (
        db_session.query(WechatGuest)
        .filter(WechatGuest.openid == "openid-guest-flow")
        .one()
    )
    assert guest.visit_count == 1


def test_wechat_unbound_login_increments_returning_guest(api_client, db_session, monkeypatch):
    set_wechat_auth_mode(monkeypatch, "optional")
    monkeypatch.setattr(
        service,
        "exchange_wechat_code_for_openid",
        lambda code: "openid-returning",
        raising=False,
    )

    api_client.post("/api/v1/auth/wechat/login", json={"code": "code-1"})
    api_client.post("/api/v1/auth/wechat/login", json={"code": "code-2"})

    guest = (
        db_session.query(WechatGuest)
        .filter(WechatGuest.openid == "openid-returning")
        .one()
    )
    assert guest.visit_count == 2


def test_wechat_bound_login_does_not_create_guest(api_client, db_session, monkeypatch):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    user.wechat_openid = "openid-member"
    db_session.commit()

    set_wechat_auth_mode(monkeypatch, "optional")
    monkeypatch.setattr(
        service,
        "exchange_wechat_code_for_openid",
        lambda code: "openid-member",
        raising=False,
    )

    response = api_client.post("/api/v1/auth/wechat/login", json={"code": "code-1"})

    assert response.status_code == 200
    assert db_session.query(WechatGuest).count() == 0
