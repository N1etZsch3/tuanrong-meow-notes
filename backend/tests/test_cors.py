from fastapi.testclient import TestClient

from app import main as main_module
from app.core.config import Settings


def test_dev_cors_allows_localhost_on_any_port(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "settings",
        Settings(
            _env_file=None,
            cors_allow_origins="",
            cors_allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:[0-9]+)?$",
        ),
    )
    client = TestClient(main_module.create_app())

    response = client.options(
        "/api/v1/auth/captcha",
        headers={
            "Origin": "http://localhost:5174",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"


def test_production_cors_allows_configured_domain_only(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "settings",
        Settings(
            _env_file=None,
            cors_allow_origins="https://trmx.fun",
            cors_allow_origin_regex="",
        ),
    )
    client = TestClient(main_module.create_app())

    allowed_response = client.options(
        "/api/v1/auth/captcha",
        headers={
            "Origin": "https://trmx.fun",
            "Access-Control-Request-Method": "GET",
        },
    )
    denied_response = client.options(
        "/api/v1/auth/captcha",
        headers={
            "Origin": "http://localhost:5174",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed_response.status_code == 200
    assert allowed_response.headers["access-control-allow-origin"] == "https://trmx.fun"
    assert denied_response.status_code == 400
