from typing import Any


def api_success(data: Any = None, trace_id: str | None = None) -> dict[str, Any]:
    return {
        "code": 0,
        "message": "success",
        "data": {} if data is None else data,
        "trace_id": trace_id or "",
    }
