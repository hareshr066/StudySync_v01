"""Deck management service."""

import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from bson import ObjectId
from pymongo.database import Database

from app.db.mongodb import get_database


class DeckService:
    """Handles deck CRUD and membership operations."""

    def __init__(self):
        self.db: Database = get_database()

    def create_deck(self, owner_id: str, title: str, description: str = "", visibility: str = "private", tags: List[str] = None) -> Dict[str, Any]:
        """Create a new deck and add owner as member."""
        now = datetime.now(timezone.utc)
        clean_tags = [t.strip().lower() for t in (tags or []) if t.strip()][:20]
        deck_doc = {
            "owner_id": owner_id,
            "title": title.strip(),
            "description": description.strip(),
            "visibility": visibility,
            "tags": clean_tags,
            "member_count": 1,
            "card_count": 0,
            "share_token": None,
            "created_at": now,
            "updated_at": now,
        }
        result = self.db.decks.insert_one(deck_doc)
        deck_id = str(result.inserted_id)

        # Add owner as deck member
        self.db.deck_members.insert_one({
            "deck_id": deck_id,
            "user_id": owner_id,
            "role": "owner",
            "joined_at": now,
        })

        return self._format_deck(deck_doc, deck_id)

    def get_deck(self, deck_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a deck by ID."""
        try:
            deck = self.db.decks.find_one({"_id": ObjectId(deck_id)})
        except Exception:
            return None
        if deck is None:
            return None
        formatted = self._format_deck(deck, str(deck["_id"]))
        # Enrich with owner name
        owner = self.db.users.find_one({"_id": ObjectId(deck["owner_id"])})
        if owner:
            formatted["owner_name"] = owner["name"]
        return formatted

    def list_user_decks(self, user_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """List all decks a user owns or is a member of."""
        # Get all deck IDs where user is a member
        memberships = self.db.deck_members.find({"user_id": user_id})
        deck_ids = [m["deck_id"] for m in memberships]

        if not deck_ids:
            return [], 0

        # Convert to ObjectIds
        object_ids = []
        for did in deck_ids:
            try:
                object_ids.append(ObjectId(did))
            except Exception:
                continue

        total = self.db.decks.count_documents({"_id": {"$in": object_ids}})
        skip = (page - 1) * page_size

        decks = list(
            self.db.decks.find({"_id": {"$in": object_ids}})
            .sort("updated_at", -1)
            .skip(skip)
            .limit(page_size)
        )

        # Get owner names
        owner_ids = list(set(d["owner_id"] for d in decks))
        owner_oids = [ObjectId(oid) for oid in owner_ids]
        owners = {str(u["_id"]): u["name"] for u in self.db.users.find({"_id": {"$in": owner_oids}})}

        result = []
        for deck in decks:
            formatted = self._format_deck(deck, str(deck["_id"]))
            formatted["owner_name"] = owners.get(deck["owner_id"], "Unknown")
            result.append(formatted)

        return result, total

    def search_decks(self, query: str, user_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """Search user's decks by title, description, or tags."""
        memberships = self.db.deck_members.find({"user_id": user_id})
        deck_ids = [m["deck_id"] for m in memberships]
        if not deck_ids:
            return [], 0

        object_ids = [ObjectId(did) for did in deck_ids if ObjectId.is_valid(did)]
        q = query.strip()
        mongo_filter = {
            "_id": {"$in": object_ids},
            "$or": [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
                {"tags": {"$regex": q, "$options": "i"}},
            ]
        }
        total = self.db.decks.count_documents(mongo_filter)
        skip = (page - 1) * page_size
        decks = list(self.db.decks.find(mongo_filter).sort("updated_at", -1).skip(skip).limit(page_size))

        owner_ids = list(set(d["owner_id"] for d in decks))
        owner_oids = [ObjectId(oid) for oid in owner_ids]
        owners = {str(u["_id"]): u["name"] for u in self.db.users.find({"_id": {"$in": owner_oids}})} if owner_oids else {}

        result = []
        for deck in decks:
            f = self._format_deck(deck, str(deck["_id"]))
            f["owner_name"] = owners.get(deck["owner_id"], "Unknown")
            result.append(f)
        return result, total

    def discover_public_decks(self, page: int = 1, page_size: int = 20, sort: str = "popular") -> Tuple[List[Dict[str, Any]], int]:
        """Discover public decks."""
        mongo_filter = {"visibility": "public"}
        total = self.db.decks.count_documents(mongo_filter)
        skip = (page - 1) * page_size

        sort_key = "member_count" if sort == "popular" else "created_at"
        sort_dir = -1

        decks = list(
            self.db.decks.find(mongo_filter)
            .sort(sort_key, sort_dir)
            .skip(skip)
            .limit(page_size)
        )

        owner_ids = list(set(d["owner_id"] for d in decks))
        owner_oids = [ObjectId(oid) for oid in owner_ids]
        owners = {str(u["_id"]): u["name"] for u in self.db.users.find({"_id": {"$in": owner_oids}})} if owner_oids else {}

        result = []
        for deck in decks:
            f = self._format_deck(deck, str(deck["_id"]))
            f["owner_name"] = owners.get(deck["owner_id"], "Unknown")
            result.append(f)
        return result, total

    def update_deck(self, deck_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a deck. Only the owner can update."""
        deck = self.db.decks.find_one({"_id": ObjectId(deck_id)})
        if deck is None:
            return None
        if deck["owner_id"] != user_id:
            raise PermissionError("Only the deck owner can update this deck")

        update_fields = {}
        for field in ["title", "description", "visibility"]:
            if field in updates and updates[field] is not None:
                update_fields[field] = updates[field].strip() if isinstance(updates[field], str) else updates[field]

        if "tags" in updates and updates["tags"] is not None:
            update_fields["tags"] = [t.strip().lower() for t in updates["tags"] if t.strip()][:20]

        if not update_fields:
            return self._format_deck(deck, deck_id)

        update_fields["updated_at"] = datetime.now(timezone.utc)
        self.db.decks.update_one({"_id": ObjectId(deck_id)}, {"$set": update_fields})

        updated = self.db.decks.find_one({"_id": ObjectId(deck_id)})
        return self._format_deck(updated, deck_id)

    def delete_deck(self, deck_id: str, user_id: str) -> bool:
        """Delete a deck and all associated data. Only the owner can delete."""
        deck = self.db.decks.find_one({"_id": ObjectId(deck_id)})
        if deck is None:
            return False
        if deck["owner_id"] != user_id:
            raise PermissionError("Only the deck owner can delete this deck")

        # Delete all associated data
        card_ids = [str(c["_id"]) for c in self.db.cards.find({"deck_id": deck_id}, {"_id": 1})]
        if card_ids:
            self.db.card_reviews.delete_many({"card_id": {"$in": card_ids}})
        self.db.cards.delete_many({"deck_id": deck_id})
        self.db.deck_members.delete_many({"deck_id": deck_id})
        self.db.rooms.delete_many({"deck_id": deck_id})
        self.db.decks.delete_one({"_id": ObjectId(deck_id)})

        return True

    def generate_share_token(self, deck_id: str, user_id: str) -> str:
        """Generate a share token for a deck. Only owner can do this."""
        deck = self.db.decks.find_one({"_id": ObjectId(deck_id)})
        if deck is None:
            raise ValueError("Deck not found")
        if deck["owner_id"] != user_id:
            raise PermissionError("Only the deck owner can share this deck")

        # Generate or return existing token
        if deck.get("share_token"):
            return deck["share_token"]

        token = secrets.token_urlsafe(32)
        self.db.decks.update_one(
            {"_id": ObjectId(deck_id)},
            {"$set": {
                "share_token": token,
                "visibility": "shared" if deck.get("visibility") == "private" else deck.get("visibility", "shared"),
                "updated_at": datetime.now(timezone.utc),
            }}
        )
        return token

    def join_deck_by_token(self, share_token: str, user_id: str) -> Dict[str, Any]:
        """Join a deck using a share token."""
        deck = self.db.decks.find_one({"share_token": share_token})
        if deck is None:
            raise ValueError("Invalid or expired share link")

        deck_id = str(deck["_id"])

        # Check if already a member
        existing = self.db.deck_members.find_one({"deck_id": deck_id, "user_id": user_id})
        if existing:
            return self._format_deck(deck, deck_id)

        # Add as member
        now = datetime.now(timezone.utc)
        self.db.deck_members.insert_one({
            "deck_id": deck_id,
            "user_id": user_id,
            "role": "member",
            "joined_at": now,
        })

        # Update member count
        member_count = self.db.deck_members.count_documents({"deck_id": deck_id})
        self.db.decks.update_one(
            {"_id": ObjectId(deck_id)},
            {"$set": {"member_count": member_count, "updated_at": now}}
        )

        updated_deck = self.db.decks.find_one({"_id": ObjectId(deck_id)})
        return self._format_deck(updated_deck, deck_id)

    def join_public_deck(self, deck_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Join a public deck."""
        deck = self.db.decks.find_one({"_id": ObjectId(deck_id)})
        if not deck or deck.get("visibility") != "public":
            return None

        existing = self.db.deck_members.find_one({"deck_id": deck_id, "user_id": user_id})
        if existing:
            return self._format_deck(deck, deck_id)

        now = datetime.now(timezone.utc)
        self.db.deck_members.insert_one({
            "deck_id": deck_id,
            "user_id": user_id,
            "role": "member",
            "joined_at": now,
        })
        mc = self.db.deck_members.count_documents({"deck_id": deck_id})
        self.db.decks.update_one({"_id": ObjectId(deck_id)}, {"$set": {"member_count": mc, "updated_at": now}})
        updated = self.db.decks.find_one({"_id": ObjectId(deck_id)})
        return self._format_deck(updated, deck_id)

    def is_member(self, deck_id: str, user_id: str) -> bool:
        """Check if a user is a member of a deck."""
        return self.db.deck_members.find_one({"deck_id": deck_id, "user_id": user_id}) is not None

    def is_owner(self, deck_id: str, user_id: str) -> bool:
        """Check if a user owns a deck."""
        deck = self.db.decks.find_one({"_id": ObjectId(deck_id)})
        return deck is not None and deck["owner_id"] == user_id

    def _format_deck(self, deck: Dict[str, Any], deck_id: str) -> Dict[str, Any]:
        """Format a deck document for API response."""
        return {
            "id": deck_id,
            "owner_id": deck.get("owner_id", ""),
            "title": deck.get("title", ""),
            "description": deck.get("description", ""),
            "visibility": deck.get("visibility", "private"),
            "member_count": deck.get("member_count", 0),
            "card_count": deck.get("card_count", 0),
            "tags": deck.get("tags", []),
            "share_token": deck.get("share_token"),
            "created_at": deck["created_at"].isoformat() if isinstance(deck.get("created_at"), datetime) else str(deck.get("created_at", "")),
            "updated_at": deck["updated_at"].isoformat() if isinstance(deck.get("updated_at"), datetime) else str(deck.get("updated_at", "")),
        }
