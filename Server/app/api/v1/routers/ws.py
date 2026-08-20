"""Realtime endpoints.

Browsers can't set an Authorization header on the WebSocket handshake, so
authenticated sockets (`/ws/user`) use a short-lived one-time ticket instead:
call GET /ws/ticket (normal authenticated HTTP request, bearer token) to
mint one, then connect to `/ws/user?ticket=...` within 30 seconds. The
ticket is single-use and stored in Redis with a TTL, never as a long-lived
credential.
"""
from __future__ import annotations

import asyncio
import secrets

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.v1.deps import get_current_user
from app.core.redis import get_redis, market_channel, user_channel
from app.models.user import User
from app.ws.manager import manager

router = APIRouter()

TICKET_TTL_SECONDS = 30
HEARTBEAT_INTERVAL_SECONDS = 30


@router.get("/ws/ticket")
async def issue_ws_ticket(user: User = Depends(get_current_user)):
    ticket = secrets.token_urlsafe(32)
    redis = get_redis()
    await redis.set(f"ws-ticket:{ticket}", str(user.id), ex=TICKET_TTL_SECONDS)
    return {"ticket": ticket, "expiresInSeconds": TICKET_TTL_SECONDS}


async def _heartbeat(ws: WebSocket) -> None:
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            await ws.send_json({"type": "ping"})
    except (asyncio.CancelledError, Exception):
        return


@router.websocket("/ws/markets/{slug}")
async def ws_market(websocket: WebSocket, slug: str):
    channel = market_channel(slug)
    await manager.connect(channel, websocket)
    heartbeat_task = asyncio.create_task(_heartbeat(websocket))
    try:
        while True:
            # We don't expect inbound client messages on this channel, but
            # awaiting receive_text() is what lets us detect disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        await manager.disconnect(channel, websocket)


@router.websocket("/ws/user")
async def ws_user(websocket: WebSocket, ticket: str):
    redis = get_redis()
    key = f"ws-ticket:{ticket}"
    user_id = await redis.get(key)
    if not user_id:
        await websocket.close(code=4401)
        return
    await redis.delete(key)  # one-time use

    channel = user_channel(user_id)
    await manager.connect(channel, websocket)
    heartbeat_task = asyncio.create_task(_heartbeat(websocket))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        await manager.disconnect(channel, websocket)
