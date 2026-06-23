from fastapi.testclient import TestClient

from app.main import app


def test_api_v1_health_returns_unified_response_envelope():
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["message"] == "success"
    assert payload["data"] == {"status": "ok", "service": "catmap-backend"}
    assert isinstance(payload["trace_id"], str)
    assert payload["trace_id"]


def test_trace_id_header_is_reused_in_response_body_and_header():
    client = TestClient(app)

    response = client.get("/api/v1/health", headers={"X-Trace-Id": "trace-from-client"})

    assert response.status_code == 200
    assert response.headers["X-Trace-Id"] == "trace-from-client"
    assert response.json()["trace_id"] == "trace-from-client"
