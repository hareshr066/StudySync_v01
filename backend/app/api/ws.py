"""WebSocket endpoint for study rooms."""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.security import decode_access_token
from app.services.room_service import RoomService
from app.realtime.manager import manager
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/api/v1/ws/rooms/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: str):
    # Authenticate via query param token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Get user name
    db = get_database()
    from bson import ObjectId
    user = db.users.find_one({"_id": ObjectId(user_id)})
    user_name = user["name"] if user else "Unknown"

    # Join room
    room_svc = RoomService()
    room_svc.join_room(room_id, user_id)

    await manager.connect(room_id, user_id, websocket)

    try:
        # Broadcast join
        await manager.broadcast(room_id, {
            "type": "user_joined",
            "data": {"user_id": user_id, "name": user_name}
        })

        # Send current presence
        online = manager.get_online_users(room_id)
        users_info = []
        for uid in online:
            u = db.users.find_one({"_id": ObjectId(uid)})
            users_info.append({"user_id": uid, "name": u["name"] if u else "Unknown", "is_online": True})

        await manager.send_personal(room_id, user_id, {
            "type": "room_state",
            "data": {"room_id": room_id, "users": users_info}
        })

        # Listen for messages
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")
                # Handle ping/pong for keepalive
                if msg_type == "ping":
                    await manager.send_personal(room_id, user_id, {"type": "pong"})
                elif msg_type == "study_update":
                    await manager.broadcast(room_id, {
                        "type": "study_update",
                        "data": {"user_id": user_id, "name": user_name, **msg.get("data", {})}
                    }, exclude_user=user_id)
                elif msg_type == "chat_message":
                    text = msg.get("data", {}).get("text", "")[:500]
                    if text:
                        from datetime import datetime, timezone
                        chat_doc = {
                            "room_id": room_id,
                            "user_id": user_id,
                            "name": user_name,
                            "message": text,
                            "created_at": datetime.now(timezone.utc)
                        }
                        db.room_messages.insert_one(chat_doc)
                        chat_doc["_id"] = str(chat_doc["_id"])
                        chat_doc["created_at"] = chat_doc["created_at"].isoformat()
                        await manager.broadcast(room_id, {
                            "type": "chat_message",
                            "data": chat_doc
                        })
                elif msg_type in ["session_start", "session_pause", "session_resume", "session_end"]:
                    # Host only check
                    room = db.rooms.find_one({"_id": ObjectId(room_id)})
                    if room and room["created_by"] == user_id:
                        await manager.broadcast(room_id, {
                            "type": msg_type,
                            "data": {"user_id": user_id, "name": user_name}
                        })
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id} in room {room_id}: {e}")
    finally:
        manager.disconnect(room_id, user_id)
        room_svc.leave_room(room_id, user_id)

        # Broadcast leave
        await manager.broadcast(room_id, {
            "type": "user_left",
            "data": {"user_id": user_id, "name": user_name}
        })

        # Broadcast updated presence
        online = manager.get_online_users(room_id)
        users_info = []
        for uid in online:
            u = db.users.find_one({"_id": ObjectId(uid)})
            users_info.append({"user_id": uid, "name": u["name"] if u else "Unknown", "is_online": True})
        await manager.broadcast(room_id, {
            "type": "presence_update",
            "data": {"users": users_info}
        })
