"""通知 WebSocket 连接注册表（进程内实现）。

当前部署为单 uvicorn 进程，进程内 dict 即可覆盖全部连接；
将来若扩展为多 worker，需要换成 Redis pub/sub 等跨进程广播。

业务代码（FastAPI 同步端点跑在线程池里）通过 notify_threadsafe 调度到
事件循环推送；WS 端点协程通过 register/unregister 维护连接。
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import WebSocket


class NotificationHub:
    def __init__(self) -> None:
        self._connections: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None

    def register(self, user_id: UUID, websocket: WebSocket) -> None:
        # 捕获事件循环，供同步线程 notify_threadsafe 调度
        self._loop = asyncio.get_running_loop()
        self._connections[user_id].add(websocket)

    def unregister(self, user_id: UUID, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    def connection_count(self, user_id: UUID) -> int:
        return len(self._connections.get(user_id, ()))

    async def push(self, user_id: UUID, payload: dict[str, Any]) -> None:
        sockets = list(self._connections.get(user_id, ()))
        if not sockets:
            return
        message = json.dumps(payload, ensure_ascii=False, default=str)
        for websocket in sockets:
            try:
                await websocket.send_text(message)
            except Exception:
                # 发送失败视为连接已死，移除
                self.unregister(user_id, websocket)

    def notify_threadsafe(self, user_ids: list[UUID], payload: dict[str, Any]) -> None:
        """从同步业务线程安全地调度推送；无在线连接或循环未捕获时为 no-op。"""
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        for user_id in user_ids:
            if self._connections.get(user_id):
                asyncio.run_coroutine_threadsafe(self.push(user_id, payload), loop)


notification_hub = NotificationHub()
