from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._channels[channel].add(websocket)

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        async with self._lock:
            if channel in self._channels:
                self._channels[channel].discard(websocket)
                if not self._channels[channel]:
                    self._channels.pop(channel, None)

    async def broadcast(self, channel: str, event: str, payload: dict[str, Any]) -> None:
        message = json.dumps({
            "event": event,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }, default=str)
        async with self._lock:
            sockets = list(self._channels.get(channel, set()))
        stale: list[WebSocket] = []
        for socket in sockets:
            try:
                await socket.send_text(message)
            except Exception:
                stale.append(socket)
        for socket in stale:
            await self.disconnect(channel, socket)

    async def heartbeat(self) -> None:
        while True:
            await asyncio.sleep(20)
            await self.broadcast("system", "heartbeat", {"status": "ok"})

    def counts(self) -> dict[str, int]:
        return {channel: len(sockets) for channel, sockets in self._channels.items()}


manager = WebSocketManager()
