from typing import Any

from fastapi.responses import JSONResponse


def api_success(data: Any = None, trace_id: str | None = None) -> dict[str, Any]:
    return {
        "code": 0,
        "message": "success",
        "data": {} if data is None else data,
        "trace_id": trace_id or "",
    }


def api_error_payload(
    *,
    code: int,
    message: str,
    trace_id: str | None = None,
    data: Any = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data,
        "trace_id": trace_id or "",
    }


def api_error_response(
    *,
    status_code: int,
    code: int,
    message: str,
    trace_id: str | None = None,
    data: Any = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=api_error_payload(code=code, message=message, trace_id=trace_id, data=data),
    )
