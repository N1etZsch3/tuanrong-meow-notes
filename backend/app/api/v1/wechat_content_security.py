import json
from xml.etree import ElementTree

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import APIError, ErrorCode
from app.db.session import get_db
from app.modules.files import service
from app.modules.files.content_security import verify_callback_signature

router = APIRouter(tags=["WeChat Content Security"])


def _require_valid_signature(
    *,
    settings: Settings,
    signature: str,
    timestamp: str,
    nonce: str,
) -> None:
    if not verify_callback_signature(
        token=settings.wechat_content_security_callback_token,
        signature=signature,
        timestamp=timestamp,
        nonce=nonce,
    ):
        raise APIError(
            code=ErrorCode.FILE_SECURITY_CALLBACK_INVALID,
            message="图片审核回调签名无效",
            status_code=403,
        )


@router.get("/events", summary="Verify WeChat content security callback")
def verify_events_callback(
    signature: str,
    timestamp: str,
    nonce: str,
    echostr: str,
    settings: Settings = Depends(get_settings),
):
    _require_valid_signature(
        settings=settings,
        signature=signature,
        timestamp=timestamp,
        nonce=nonce,
    )
    return PlainTextResponse(echostr)


@router.post("/events", summary="Receive WeChat content security result")
async def receive_events_callback(
    request: Request,
    signature: str,
    timestamp: str,
    nonce: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    _require_valid_signature(
        settings=settings,
        signature=signature,
        timestamp=timestamp,
        nonce=nonce,
    )
    payload = _parse_callback_body(await request.body())
    event = str(payload.get("Event") or payload.get("event") or "").strip()
    if event and event != "wxa_media_check":
        return PlainTextResponse("success")
    service.handle_security_callback(db, payload)
    return PlainTextResponse("success")


def _parse_callback_body(body: bytes) -> dict:
    try:
        payload = json.loads(body.decode("utf-8"))
        if isinstance(payload, dict):
            return payload
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass

    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError as exc:
        raise APIError(
            code=ErrorCode.FILE_SECURITY_CALLBACK_INVALID,
            message="图片审核回调内容无效",
            status_code=400,
        ) from exc
    payload = {child.tag: child.text or "" for child in root}
    for key in ("result", "detail"):
        value = payload.get(key)
        if isinstance(value, str):
            try:
                payload[key] = json.loads(value)
            except json.JSONDecodeError:
                continue
    return payload
