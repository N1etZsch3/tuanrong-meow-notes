import json
from urllib.error import URLError

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import APIError, ErrorCode


def test_wechat_auth_settings_default_to_safe_off_mode():
    settings = Settings(_env_file=None)

    assert settings.wechat_miniapp_appid == ""
    assert settings.wechat_miniapp_secret == ""
    assert settings.wechat_auth_mode == "off"


def test_wechat_auth_mode_rejects_unknown_values():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, wechat_auth_mode="strict")


def test_exchange_wechat_code_for_openid_returns_openid(monkeypatch):
    from app.modules.auth import wechat

    captured_url = ""

    def fake_fetch_json(url: str, timeout: float) -> dict:
        nonlocal captured_url
        captured_url = url
        assert timeout == 3.0
        return {"openid": "openid-member-1", "session_key": "session-key-value"}

    monkeypatch.setattr(wechat, "_fetch_json", fake_fetch_json)

    settings = Settings(
        _env_file=None,
        wechat_miniapp_appid="miniapp-id",
        wechat_miniapp_secret="miniapp-secret",
    )

    openid = wechat.exchange_wechat_code_for_openid("login-code-1", settings=settings)

    assert openid == "openid-member-1"
    assert "appid=miniapp-id" in captured_url
    assert "secret=miniapp-secret" in captured_url
    assert "js_code=login-code-1" in captured_url
    assert "grant_type=authorization_code" in captured_url


def test_exchange_wechat_code_for_openid_rejects_missing_server_config():
    from app.modules.auth import wechat

    settings = Settings(_env_file=None, wechat_miniapp_appid="", wechat_miniapp_secret="")

    with pytest.raises(APIError) as exc_info:
        wechat.exchange_wechat_code_for_openid("login-code-1", settings=settings)

    assert exc_info.value.code == ErrorCode.SERVER_ERROR
    assert exc_info.value.status_code == 500


@pytest.mark.parametrize(
    "payload",
    [
        {"errcode": 40029, "errmsg": "invalid code"},
        {"session_key": "session-key-value"},
    ],
)
def test_exchange_wechat_code_for_openid_rejects_wechat_error_payload(
    monkeypatch,
    payload: dict,
):
    from app.modules.auth import wechat

    monkeypatch.setattr(wechat, "_fetch_json", lambda _url, _timeout: payload)
    settings = Settings(
        _env_file=None,
        wechat_miniapp_appid="miniapp-id",
        wechat_miniapp_secret="miniapp-secret",
    )

    with pytest.raises(APIError) as exc_info:
        wechat.exchange_wechat_code_for_openid("login-code-1", settings=settings)

    assert exc_info.value.code == ErrorCode.PARAM_ERROR
    assert exc_info.value.status_code == 400


def test_exchange_wechat_code_for_openid_wraps_network_failures(monkeypatch):
    from app.modules.auth import wechat

    def raise_network_error(_url: str, _timeout: float) -> dict:
        raise URLError("network unavailable")

    monkeypatch.setattr(wechat, "_fetch_json", raise_network_error)
    settings = Settings(
        _env_file=None,
        wechat_miniapp_appid="miniapp-id",
        wechat_miniapp_secret="miniapp-secret",
    )

    with pytest.raises(APIError) as exc_info:
        wechat.exchange_wechat_code_for_openid("login-code-1", settings=settings)

    assert exc_info.value.code == ErrorCode.SERVER_ERROR
    assert exc_info.value.status_code == 502


def test_fetch_json_decodes_response(monkeypatch):
    from app.modules.auth import wechat

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _tb):
            return None

        def read(self) -> bytes:
            return json.dumps({"openid": "openid-member-1"}).encode("utf-8")

    monkeypatch.setattr(wechat.request, "urlopen", lambda _url, timeout: FakeResponse())

    assert wechat._fetch_json("https://example.invalid", 3.0) == {
        "openid": "openid-member-1"
    }
