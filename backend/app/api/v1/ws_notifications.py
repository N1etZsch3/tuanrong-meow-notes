"""通知实时推送 WebSocket 端点。

全路径 `/api/v1/ws/notifications?token=<accessToken>`（前端
services/notification-socket.ts 由 API base 推导）。信封：
  服务端 → {"type": "notification.new", "data": NotificationItemDto}
  客户端 → {"type": "ping"}，服务端回 {"type": "pong"}
鉴权失败以 4401 关闭。
"""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.notifications.hub import notification_hub

router = APIRouter()

WS_AUTH_FAILED = 4401


def _authenticate(db: Session, token: str) -> UUID | None:
    """校验 token 并返回用户 id；口径与 get_current_user 一致。"""
    try:
        payload = decode_access_token(token)
        user_id = UUID(str(payload.get("sub")))
        token_version = int(payload.get("token_version", -1))
    except Exception:
        return None

    user = db.get(User, user_id)
    if (
        user is None
        or user.deleted_at is not None
        or user.status != "active"
        or token_version != user.token_version
    ):
        return None
    return user_id


@router.websocket("/ws/notifications")
async def notifications_socket(
    websocket: WebSocket,
    token: str = Query(default=""),
    db: Session = Depends(get_db),
):
    user_id = _authenticate(db, token)
    if user_id is None:
        await websocket.close(code=WS_AUTH_FAILED)
        return

    await websocket.accept()
    notification_hub.register(user_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(message, dict) and message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    finally:
        notification_hub.unregister(user_id, websocket)
