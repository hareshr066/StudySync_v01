"""WebSocket connection manager for study rooms."""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for study rooms. In-memory for MVP."""

    def __init__(self):
        # room_id -> set of (user_id, websocket)
        self._rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, room_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self._rooms:
            self._rooms[room_id] = {}
        # Close existing connection for same user in same room
        if user_id in self._rooms[room_id]:
            try:
                await self._rooms[room_id][user_id].close()
            except Exception:
                pass
        self._rooms[room_id][user_id] = websocket
        logger.info(f"User {user_id} connected to room {room_id}")

    def disconnect(self, room_id: str, user_id: str):
        if room_id in self._rooms:
            self._rooms[room_id].pop(user_id, None)
            if not self._rooms[room_id]:
                del self._rooms[room_id]
        logger.info(f"User {user_id} disconnected from room {room_id}")

    async def broadcast(self, room_id: str, message: dict, exclude_user: str = None):
        if room_id not in self._rooms:
            return
        dead = []
        for uid, ws in self._rooms[room_id].items():
            if uid == exclude_user:
                continue
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(uid)
        for uid in dead:
            self.disconnect(room_id, uid)

    async def send_personal(self, room_id: str, user_id: str, message: dict):
        if room_id in self._rooms and user_id in self._rooms[room_id]:
            try:
                await self._rooms[room_id][user_id].send_text(json.dumps(message))
            except Exception:
                self.disconnect(room_id, user_id)

    def get_online_users(self, room_id: str) -> list:
        if room_id not in self._rooms:
            return []
        return list(self._rooms[room_id].keys())

    def is_user_connected(self, room_id: str, user_id: str) -> bool:
        return room_id in self._rooms and user_id in self._rooms[room_id]


# Global singleton
manager = ConnectionManager()
