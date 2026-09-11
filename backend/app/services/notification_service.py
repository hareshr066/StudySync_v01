"""Notification service."""

from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

from bson import ObjectId
from app.db.mongodb import get_database


class NotificationService:
    """Handles in-app notifications."""

    def __init__(self):
        self.db = get_database()

    def create(self, user_id: str, ntype: str, title: str, message: str) -> Dict[str, Any]:
        """Create a notification."""
        now = datetime.now(timezone.utc)
        doc = {
            "user_id": user_id,
            "type": ntype,
            "title": title,
            "message": message,
            "read": False,
            "created_at": now,
        }
        result = self.db.notifications.insert_one(doc)
        return self._format(doc, str(result.inserted_id))

    def list_for_user(self, user_id: str, limit: int = 50) -> Tuple[List[Dict[str, Any]], int, int]:
        """Return notifications, total count, and unread count."""
        total = self.db.notifications.count_documents({"user_id": user_id})
        unread = self.db.notifications.count_documents({"user_id": user_id, "read": False})
        notes = list(
            self.db.notifications.find({"user_id": user_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        items = [self._format(n, str(n["_id"])) for n in notes]
        return items, total, unread

    def mark_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a single notification as read."""
        result = self.db.notifications.update_one(
            {"_id": ObjectId(notification_id), "user_id": user_id},
            {"$set": {"read": True}}
        )
        return result.modified_count > 0

    def mark_all_read(self, user_id: str) -> int:
        """Mark all notifications as read."""
        result = self.db.notifications.update_many(
            {"user_id": user_id, "read": False},
            {"$set": {"read": True}}
        )
        return result.modified_count

    def _format(self, doc: Dict, nid: str) -> Dict[str, Any]:
        return {
            "id": nid,
            "type": doc.get("type", ""),
            "title": doc.get("title", ""),
            "message": doc.get("message", ""),
            "read": doc.get("read", False),
            "created_at": doc["created_at"].isoformat() if isinstance(doc.get("created_at"), datetime) else "",
        }
