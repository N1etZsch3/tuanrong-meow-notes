from fastapi.testclient import TestClient

from app.main import app


def test_dev_cors_allows_localhost_on_any_port():
    client = TestClient(app)

    response = client.options(
        "/api/v1/auth/captcha",
        headers={
            "Origin": "http://localhost:5174",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"
