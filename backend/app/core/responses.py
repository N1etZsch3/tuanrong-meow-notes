from typing import Any

from fastapi.responses import JSONResponse

_UNSET = object()

def api_success(
    data: Any = _UNSET,
    trace_id: str | None = None,
    message: str = "success",
) -> dict[str, Any]:
    return {
        "code": 0,
        "message": message,
        "data": {} if data is _UNSET else data,
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
