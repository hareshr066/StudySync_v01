"""Card management service."""

import csv
import io
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from bson import ObjectId
from pymongo.database import Database

from app.db.mongodb import get_database


class CardService:
    """Handles card CRUD operations."""

    def __init__(self):
        self.db: Database = get_database()

    def create_card(self, deck_id: str, front: str, back: str, created_by: str, tags: List[str] = None, hint: str = "") -> Dict[str, Any]:
        """Create a new card in a deck."""
        now = datetime.now(timezone.utc)
        clean_tags = [t.strip().lower() for t in (tags or []) if t.strip()][:20]
        card_doc = {
            "deck_id": deck_id,
            "front": front.strip(),
            "back": back.strip(),
            "tags": clean_tags,
            "hint": hint.strip() if hint else "",
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
        }
        result = self.db.cards.insert_one(card_doc)
        card_id = str(result.inserted_id)

        # Update deck card count
        card_count = self.db.cards.count_documents({"deck_id": deck_id})
        self.db.decks.update_one(
            {"_id": ObjectId(deck_id)},
            {"$set": {"card_count": card_count, "updated_at": now}}
        )

        return self._format_card(card_doc, card_id)

    def get_card(self, card_id: str) -> Optional[Dict[str, Any]]:
        """Get a card by ID."""
        try:
            card = self.db.cards.find_one({"_id": ObjectId(card_id)})
        except Exception:
            return None
        if card is None:
            return None
        return self._format_card(card, str(card["_id"]))

    def list_cards(self, deck_id: str, page: int = 1, page_size: int = 50) -> Tuple[List[Dict[str, Any]], int]:
        """List cards in a deck with pagination."""
        total = self.db.cards.count_documents({"deck_id": deck_id})
        skip = (page - 1) * page_size

        cards = list(
            self.db.cards.find({"deck_id": deck_id})
            .sort("created_at", 1)
            .skip(skip)
            .limit(page_size)
        )

        result = [self._format_card(c, str(c["_id"])) for c in cards]
        return result, total

    def update_card(self, card_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a card."""
        update_fields = {}
        for field in ["front", "back", "hint"]:
            if field in updates and updates[field] is not None:
                update_fields[field] = updates[field].strip()

        if "tags" in updates and updates["tags"] is not None:
            update_fields["tags"] = [t.strip().lower() for t in updates["tags"] if t.strip()][:20]

        if not update_fields:
            card = self.db.cards.find_one({"_id": ObjectId(card_id)})
            return self._format_card(card, card_id) if card else None

        update_fields["updated_at"] = datetime.now(timezone.utc)
        self.db.cards.update_one({"_id": ObjectId(card_id)}, {"$set": update_fields})

        card = self.db.cards.find_one({"_id": ObjectId(card_id)})
        return self._format_card(card, card_id) if card else None

    def delete_card(self, card_id: str) -> bool:
        """Delete a card and associated reviews."""
        card = self.db.cards.find_one({"_id": ObjectId(card_id)})
        if card is None:
            return False

        deck_id = card["deck_id"]

        # Delete reviews for this card
        self.db.card_reviews.delete_many({"card_id": card_id})

        # Delete the card
        self.db.cards.delete_one({"_id": ObjectId(card_id)})

        # Update deck card count
        card_count = self.db.cards.count_documents({"deck_id": deck_id})
        self.db.decks.update_one(
            {"_id": ObjectId(deck_id)},
            {"$set": {"card_count": card_count, "updated_at": datetime.now(timezone.utc)}}
        )

        return True

    def import_csv(self, deck_id: str, csv_content: str, created_by: str) -> Dict[str, Any]:
        """Import cards from CSV. Format: front,back,tags (tags optional, comma-separated in quotes)."""
        imported = 0
        skipped = 0
        errors = 0
        details = []
        now = datetime.now(timezone.utc)

        try:
            reader = csv.reader(io.StringIO(csv_content))
            header = next(reader, None)
            if not header:
                return {"imported": 0, "skipped": 0, "errors": 1, "details": ["Empty CSV"]}

            # Normalize header
            header_lower = [h.strip().lower() for h in header]
            front_idx = header_lower.index("front") if "front" in header_lower else 0
            back_idx = header_lower.index("back") if "back" in header_lower else 1
            tags_idx = header_lower.index("tags") if "tags" in header_lower else None

            for row_num, row in enumerate(reader, start=2):
                if len(row) < 2:
                    errors += 1
                    details.append(f"Row {row_num}: missing front or back")
                    continue

                front = row[front_idx].strip() if front_idx < len(row) else ""
                back = row[back_idx].strip() if back_idx < len(row) else ""

                if not front or not back:
                    errors += 1
                    details.append(f"Row {row_num}: empty front or back")
                    continue

                tags = []
                if tags_idx is not None and tags_idx < len(row):
                    tags = [t.strip().lower() for t in row[tags_idx].split(",") if t.strip()]

                self.db.cards.insert_one({
                    "deck_id": deck_id,
                    "front": front,
                    "back": back,
                    "tags": tags[:20],
                    "hint": "",
                    "created_by": created_by,
                    "created_at": now,
                    "updated_at": now,
                })
                imported += 1

        except Exception as e:
            errors += 1
            details.append(f"CSV parse error: {str(e)[:100]}")

        # Update deck card count
        card_count = self.db.cards.count_documents({"deck_id": deck_id})
        self.db.decks.update_one(
            {"_id": ObjectId(deck_id)},
            {"$set": {"card_count": card_count, "updated_at": now}}
        )

        return {"imported": imported, "skipped": skipped, "errors": errors, "details": details[:20]}

    def export_csv(self, deck_id: str) -> str:
        """Export deck cards as CSV."""
        cards = list(self.db.cards.find({"deck_id": deck_id}).sort("created_at", 1))
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["front", "back", "tags"])
        for card in cards:
            tags = ",".join(card.get("tags", []))
            writer.writerow([card["front"], card["back"], tags])
        return output.getvalue()

    def _format_card(self, card: Dict[str, Any], card_id: str) -> Dict[str, Any]:
        """Format a card document for API response."""
        return {
            "id": card_id,
            "deck_id": card.get("deck_id", ""),
            "front": card.get("front", ""),
            "back": card.get("back", ""),
            "tags": card.get("tags", []),
            "hint": card.get("hint", ""),
            "created_by": card.get("created_by", ""),
            "created_at": card["created_at"].isoformat() if isinstance(card.get("created_at"), datetime) else str(card.get("created_at", "")),
            "updated_at": card["updated_at"].isoformat() if isinstance(card.get("updated_at"), datetime) else str(card.get("updated_at", "")),
        }
