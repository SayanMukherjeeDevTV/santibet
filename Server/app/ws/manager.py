"""In-process WebSocket connection registry, fed by Redis pubsub so it fans
out correctly even when running multiple Uvicorn/Gunicorn worker processes
(a message published by worker A reaches clients connected to worker B).

One Redis pubsub subscription is kept per channel that has at least one
local subscriber; it's torn down again once the last local client for that
channel disconnects.
"""
from __future__ import annotations

import asyncio
import contextlib

from fastapi import WebSocket

from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._pubsub_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(channel, set()).add(websocket)
            if channel not in self._pubsub_tasks:
                self._pubsub_tasks[channel] = asyncio.create_task(self._listen(channel))

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(channel)
            if conns and websocket in conns:
                conns.remove(websocket)
            if conns is not None and not conns:
                self._connections.pop(channel, None)
                task = self._pubsub_tasks.pop(channel, None)
                if task:
                    task.cancel()

    async def _listen(self, channel: str) -> None:
        redis = get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = message["data"]
                dead: list[WebSocket] = []
                for ws in list(self._connections.get(channel, set())):
                    try:
                        await ws.send_text(data)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    await self.disconnect(channel, ws)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("ws_pubsub_listener_error", channel=channel)
        finally:
            with contextlib.suppress(Exception):
                await pubsub.unsubscribe(channel)
                await pubsub.close()


manager = ConnectionManager()
