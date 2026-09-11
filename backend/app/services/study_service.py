"""Study service: manages review state and study sessions."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId
from app.db.mongodb import get_database
from app.services.sm2 import calculate_sm2, rating_to_quality


class StudyService:
    def __init__(self):
        self.db = get_database()

    def get_next_card(self, deck_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get next card to study: due cards first, then new cards."""
        now = datetime.now(timezone.utc)
        all_cards = list(self.db.cards.find({"deck_id": deck_id}))
        if not all_cards:
            return None

        card_ids = [str(c["_id"]) for c in all_cards]
        reviews = {r["card_id"]: r for r in self.db.card_reviews.find(
            {"user_id": user_id, "card_id": {"$in": card_ids}}
        )}

        # Priority 1: due cards (sorted by due_at ascending)
        due_cards = []
        for card in all_cards:
            cid = str(card["_id"])
            review = reviews.get(cid)
            if review and review.get("due_at") and review["due_at"] <= now:
                due_cards.append((card, review))
        due_cards.sort(key=lambda x: x[1]["due_at"])
        if due_cards:
            card, review = due_cards[0]
            return self._format_study_card(card, review, is_new=False)

        # Priority 2: new cards (never reviewed)
        for card in all_cards:
            cid = str(card["_id"])
            if cid not in reviews:
                return self._format_study_card(card, None, is_new=True)

        return None  # All cards reviewed and not yet due

    def submit_review(self, user_id: str, card_id: str, rating: str) -> Dict[str, Any]:
        """Process a review submission using SM-2."""
        now = datetime.now(timezone.utc)
        quality = rating_to_quality(rating)

        existing = self.db.card_reviews.find_one({"user_id": user_id, "card_id": card_id})

        if existing:
            result = calculate_sm2(
                quality=quality,
                repetitions=existing.get("repetitions", 0),
                interval=existing.get("interval", 0),
                ease_factor=existing.get("ease_factor", 2.5),
                review_time=now,
            )
            self.db.card_reviews.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "repetitions": result.repetitions,
                    "interval": result.interval,
                    "ease_factor": result.ease_factor,
                    "last_reviewed_at": now,
                    "due_at": result.due_at,
                    "updated_at": now,
                }}
            )
        else:
            result = calculate_sm2(quality=quality, review_time=now)
            self.db.card_reviews.update_one(
                {"user_id": user_id, "card_id": card_id},
                {"$set": {
                    "user_id": user_id,
                    "card_id": card_id,
                    "repetitions": result.repetitions,
                    "interval": result.interval,
                    "ease_factor": result.ease_factor,
                    "last_reviewed_at": now,
                    "due_at": result.due_at,
                    "created_at": now,
                    "updated_at": now,
                }},
                upsert=True,
            )

        return {
            "card_id": card_id,
            "repetitions": result.repetitions,
            "interval": result.interval,
            "ease_factor": result.ease_factor,
            "due_at": result.due_at.isoformat(),
        }

    def get_deck_stats(self, deck_id: str, user_id: str) -> Dict[str, Any]:
        """Get study stats for a deck."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_cards = self.db.cards.count_documents({"deck_id": deck_id})
        card_ids = [str(c["_id"]) for c in self.db.cards.find({"deck_id": deck_id}, {"_id": 1})]

        if not card_ids:
            return {"total_cards": 0, "cards_studied": 0, "cards_due": 0,
                    "cards_due_today": 0, "new_cards": 0, "reviewed_today": 0, "deck_progress": 0.0}

        reviews = list(self.db.card_reviews.find({"user_id": user_id, "card_id": {"$in": card_ids}}))
        reviewed_card_ids = {r["card_id"] for r in reviews}

        cards_studied = len(reviewed_card_ids)
        cards_due = sum(1 for r in reviews if r.get("due_at") and r["due_at"] <= now)
        cards_due_today = sum(1 for r in reviews if r.get("due_at") and r["due_at"] <= now)
        new_cards = total_cards - cards_studied
        reviewed_today = sum(1 for r in reviews if r.get("last_reviewed_at") and r["last_reviewed_at"] >= today_start)
        progress = (cards_studied / total_cards * 100) if total_cards > 0 else 0.0

        return {
            "total_cards": total_cards,
            "cards_studied": cards_studied,
            "cards_due": cards_due,
            "cards_due_today": cards_due_today,
            "new_cards": new_cards,
            "reviewed_today": reviewed_today,
            "deck_progress": round(progress, 1),
        }

    def get_overall_stats(self, user_id: str) -> Dict[str, Any]:
        """Get overall study stats across all decks."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        memberships = list(self.db.deck_members.find({"user_id": user_id}))
        deck_ids = [m["deck_id"] for m in memberships]

        if not deck_ids:
            return {"total_cards": 0, "cards_studied": 0, "cards_due": 0,
                    "cards_due_today": 0, "new_cards": 0, "reviewed_today": 0, "deck_progress": 0.0}

        oids = []
        for did in deck_ids:
            try:
                oids.append(ObjectId(did))
            except Exception:
                continue

        total_cards = self.db.cards.count_documents({"deck_id": {"$in": deck_ids}})
        all_card_ids = [str(c["_id"]) for c in self.db.cards.find({"deck_id": {"$in": deck_ids}}, {"_id": 1})]

        reviews = list(self.db.card_reviews.find({"user_id": user_id, "card_id": {"$in": all_card_ids}})) if all_card_ids else []
        reviewed_ids = {r["card_id"] for r in reviews}

        cards_studied = len(reviewed_ids)
        cards_due = sum(1 for r in reviews if r.get("due_at") and r["due_at"] <= now)
        new_cards = total_cards - cards_studied
        reviewed_today = sum(1 for r in reviews if r.get("last_reviewed_at") and r["last_reviewed_at"] >= today_start)
        progress = (cards_studied / total_cards * 100) if total_cards > 0 else 0.0

        return {
            "total_cards": total_cards,
            "cards_studied": cards_studied,
            "cards_due": cards_due,
            "cards_due_today": cards_due,
            "new_cards": new_cards,
            "reviewed_today": reviewed_today,
            "deck_progress": round(progress, 1),
        }

    def _format_study_card(self, card, review, is_new):
        return {
            "id": str(card["_id"]),
            "deck_id": card["deck_id"],
            "front": card["front"],
            "back": card["back"],
            "is_new": is_new,
            "repetitions": review.get("repetitions", 0) if review else 0,
            "interval": review.get("interval", 0) if review else 0,
            "ease_factor": review.get("ease_factor", 2.5) if review else 2.5,
            "due_at": review["due_at"].isoformat() if review and review.get("due_at") else None,
        }
