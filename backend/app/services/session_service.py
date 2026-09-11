"""Study session tracking service."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from bson import ObjectId
from app.db.mongodb import get_database


def _to_utc(dt: Any) -> Optional[datetime]:
    """Ensure datetime is offset-aware UTC. If naive, attach UTC timezone."""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return None


class SessionService:
    """Tracks study sessions for analytics."""

    def __init__(self):
        self.db = get_database()

    def start_session(self, user_id: str, deck_id: str) -> Dict[str, Any]:
        """Start a new study session."""
        now = datetime.now(timezone.utc)
        doc = {
            "user_id": user_id,
            "deck_id": deck_id,
            "started_at": now,
            "ended_at": None,
            "cards_reviewed": 0,
            "duration_seconds": 0,
            "created_at": now,
        }
        res = self.db.study_sessions.insert_one(doc)
        doc["_id"] = res.inserted_id
        return self._format(doc, str(res.inserted_id))

    def end_session(self, session_id: str, user_id: str, cards_reviewed: int) -> Optional[Dict[str, Any]]:
        """End a study session and calculate duration."""
        try:
            session = self.db.study_sessions.find_one({"_id": ObjectId(session_id), "user_id": user_id})
        except Exception:
            return None
        if not session:
            return None

        now = datetime.now(timezone.utc)
        started = _to_utc(session.get("started_at"))
        duration = int((now - started).total_seconds()) if started else 0

        self.db.study_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {
                "ended_at": now,
                "cards_reviewed": cards_reviewed,
                "duration_seconds": duration,
            }}
        )

        # Update streak
        self._update_streak(user_id, now)

        updated = self.db.study_sessions.find_one({"_id": ObjectId(session_id)})
        return self._format(updated, session_id)

    def list_sessions(self, user_id: str, limit: int = 50) -> Tuple[List[Dict[str, Any]], int]:
        """List user's study sessions."""
        total = self.db.study_sessions.count_documents({"user_id": user_id})
        sessions = list(
            self.db.study_sessions.find({"user_id": user_id})
            .sort("started_at", -1)
            .limit(limit)
        )

        # Enrich with deck titles
        deck_ids = list(set(s.get("deck_id", "") for s in sessions))
        deck_oids = []
        for did in deck_ids:
            try:
                deck_oids.append(ObjectId(did))
            except Exception:
                continue
        decks = {str(d["_id"]): d["title"] for d in self.db.decks.find({"_id": {"$in": deck_oids}})} if deck_oids else {}

        result = []
        for s in sessions:
            f = self._format(s, str(s["_id"]))
            f["deck_title"] = decks.get(s.get("deck_id", ""), "")
            result.append(f)

        return result, total

    def _update_streak(self, user_id: str, now: datetime) -> None:
        """Update user's study streak after a session ends."""
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        user = self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return

        last_study = _to_utc(user.get("last_study_date"))
        current_streak = user.get("current_streak", 0)
        longest_streak = user.get("longest_streak", 0)

        if last_study:
            last_day = last_study.replace(hour=0, minute=0, second=0, microsecond=0)
            diff = (today - last_day).days
            if diff == 0:
                # Already studied today, no change
                return
            elif diff == 1:
                # Consecutive day
                current_streak += 1
            else:
                # Streak broken
                current_streak = 1
        else:
            current_streak = 1

        longest_streak = max(longest_streak, current_streak)

        self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "last_study_date": now,
            }}
        )

    def _format(self, doc: Dict, sid: str) -> Dict[str, Any]:
        return {
            "id": sid,
            "deck_id": doc.get("deck_id", ""),
            "started_at": doc["started_at"].isoformat() if isinstance(doc.get("started_at"), datetime) else "",
            "ended_at": doc["ended_at"].isoformat() if isinstance(doc.get("ended_at"), datetime) else None,
            "cards_reviewed": doc.get("cards_reviewed", 0),
            "duration_seconds": doc.get("duration_seconds", 0),
        }
