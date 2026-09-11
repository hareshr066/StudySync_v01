"""Room management service."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from bson import ObjectId
from app.db.mongodb import get_database


class RoomService:
    def __init__(self):
        self.db = get_database()

    def create_room(self, deck_id: str, name: str, created_by: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        room_doc = {
            "deck_id": deck_id, "created_by": created_by, "name": name.strip(),
            "status": "active", "created_at": now, "started_at": now, "ended_at": None,
        }
        result = self.db.rooms.insert_one(room_doc)
        room_id = str(result.inserted_id)
        self.db.room_members.insert_one({
            "room_id": room_id, "user_id": created_by, "status": "online",
            "joined_at": now, "last_seen_at": now,
        })
        return self._format_room(room_doc, room_id)

    def get_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        try:
            room = self.db.rooms.find_one({"_id": ObjectId(room_id)})
        except Exception:
            return None
        if not room:
            return None
        formatted = self._format_room(room, str(room["_id"]))
        deck = self.db.decks.find_one({"_id": ObjectId(room["deck_id"])}) if room.get("deck_id") else None
        if deck:
            formatted["deck_title"] = deck["title"]
        creator = self.db.users.find_one({"_id": ObjectId(room["created_by"])}) if room.get("created_by") else None
        if creator:
            formatted["creator_name"] = creator["name"]
        return formatted

    def list_rooms(self, deck_id: Optional[str] = None, status: str = "active") -> Tuple[List[Dict], int]:
        query = {"status": status}
        if deck_id:
            query["deck_id"] = deck_id
        rooms = list(self.db.rooms.find(query).sort("created_at", -1).limit(50))
        result = []
        for room in rooms:
            f = self._format_room(room, str(room["_id"]))
            deck = self.db.decks.find_one({"_id": ObjectId(room["deck_id"])}) if room.get("deck_id") else None
            if deck:
                f["deck_title"] = deck["title"]
            mc = self.db.room_members.count_documents({"room_id": str(room["_id"])})
            f["member_count"] = mc
            result.append(f)
        return result, len(result)

    def join_room(self, room_id: str, user_id: str) -> bool:
        room = self.db.rooms.find_one({"_id": ObjectId(room_id)})
        if not room or room["status"] != "active":
            return False
        now = datetime.now(timezone.utc)
        existing = self.db.room_members.find_one({"room_id": room_id, "user_id": user_id})
        if existing:
            self.db.room_members.update_one({"_id": existing["_id"]}, {"$set": {"status": "online", "last_seen_at": now}})
        else:
            self.db.room_members.insert_one({
                "room_id": room_id, "user_id": user_id, "status": "online",
                "joined_at": now, "last_seen_at": now,
            })
        return True

    def leave_room(self, room_id: str, user_id: str) -> bool:
        result = self.db.room_members.update_one(
            {"room_id": room_id, "user_id": user_id},
            {"$set": {"status": "offline", "last_seen_at": datetime.now(timezone.utc)}}
        )
        return result.modified_count > 0

    def end_room(self, room_id: str, user_id: str) -> bool:
        room = self.db.rooms.find_one({"_id": ObjectId(room_id)})
        if not room or room["created_by"] != user_id:
            return False
        self.db.rooms.update_one({"_id": ObjectId(room_id)}, {"$set": {"status": "ended", "ended_at": datetime.now(timezone.utc)}})
        return True

    def get_room_members(self, room_id: str) -> List[Dict[str, Any]]:
        members = list(self.db.room_members.find({"room_id": room_id}))
        result = []
        for m in members:
            user = self.db.users.find_one({"_id": ObjectId(m["user_id"])})
            result.append({
                "user_id": m["user_id"],
                "name": user["name"] if user else "Unknown",
                "status": m.get("status", "offline"),
                "joined_at": m["joined_at"].isoformat() if isinstance(m.get("joined_at"), datetime) else "",
                "is_online": m.get("status") == "online",
            })
        return result

    def _format_room(self, room, room_id):
        return {
            "id": room_id,
            "deck_id": room.get("deck_id", ""),
            "created_by": room.get("created_by", ""),
            "name": room.get("name", ""),
            "status": room.get("status", "active"),
            "member_count": 0,
            "created_at": room["created_at"].isoformat() if isinstance(room.get("created_at"), datetime) else "",
            "started_at": room["started_at"].isoformat() if isinstance(room.get("started_at"), datetime) else None,
            "ended_at": room["ended_at"].isoformat() if isinstance(room.get("ended_at"), datetime) else None,
        }
