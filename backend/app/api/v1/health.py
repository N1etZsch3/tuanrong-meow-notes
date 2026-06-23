from fastapi import APIRouter, Request

from app.core.responses import api_success

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
def health_check(request: Request):
    return api_success(
        data={"status": "ok", "service": "catmap-backend"},
        trace_id=request.state.trace_id,
    )
