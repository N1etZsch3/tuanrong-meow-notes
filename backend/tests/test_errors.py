from fastapi import Body, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import APIError, ErrorCode
from app.core.exception_handlers import register_exception_handlers
from app.core.trace import TraceIdMiddleware

PAYLOAD_BODY = Body(...)


def create_test_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)
    register_exception_handlers(app)

    class Payload(BaseModel):
        name: str

    @app.get("/api-error")
    def api_error():
        raise APIError(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="资源不存在",
            status_code=404,
        )

    @app.post("/validation-error")
    def validation_error(payload: Payload = PAYLOAD_BODY):
        return payload

    return TestClient(app)


def test_api_error_uses_unified_response_envelope():
    client = create_test_client()

    response = client.get("/api-error", headers={"X-Trace-Id": "error-trace"})

    assert response.status_code == 404
    assert response.json() == {
        "code": 40401,
        "message": "资源不存在",
        "data": None,
        "trace_id": "error-trace",
    }


def test_validation_error_uses_unified_response_envelope():
    client = create_test_client()

    response = client.post("/validation-error", json={}, headers={"X-Trace-Id": "invalid-trace"})

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == 40001
    assert payload["message"] == "参数错误"
    assert payload["trace_id"] == "invalid-trace"
    assert isinstance(payload["data"]["errors"], list)
