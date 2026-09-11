"""Authentication service: registration, login, token management."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.db.mongodb import get_database


class AuthService:
    """Handles user authentication operations."""

    def __init__(self):
        self.db: Database = get_database()

    def register(self, name: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user."""
        # Normalize email
        normalized_email = email.strip().lower()

        now = datetime.now(timezone.utc)
        user_doc = {
            "name": name.strip(),
            "email": normalized_email,
            "password_hash": hash_password(password),
            "avatar_url": None,
            "created_at": now,
            "updated_at": now,
        }

        try:
            result = self.db.users.insert_one(user_doc)
        except DuplicateKeyError:
            raise ValueError("A user with this email already exists")

        user_id = str(result.inserted_id)
        tokens = self._generate_tokens(user_id)

        return {
            "user": {
                "id": user_id,
                "name": user_doc["name"],
                "email": user_doc["email"],
                "avatar_url": user_doc["avatar_url"],
                "created_at": now.isoformat(),
            },
            "tokens": tokens,
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate a user and return tokens."""
        normalized_email = email.strip().lower()
        user = self.db.users.find_one({"email": normalized_email})

        if user is None:
            raise ValueError("Invalid email or password")

        if not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid email or password")

        user_id = str(user["_id"])
        tokens = self._generate_tokens(user_id)

        return {
            "user": {
                "id": user_id,
                "name": user["name"],
                "email": user["email"],
                "avatar_url": user.get("avatar_url"),
                "created_at": user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else str(user["created_at"]),
            },
            "tokens": tokens,
        }

    def refresh_tokens(self, user_id: str) -> Dict[str, str]:
        """Generate new access and refresh tokens."""
        user = self.db.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise ValueError("User not found")
        return self._generate_tokens(user_id)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        user = self.db.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            return None
        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "avatar_url": user.get("avatar_url"),
            "created_at": user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else str(user["created_at"]),
        }

    def _generate_tokens(self, user_id: str) -> Dict[str, str]:
        """Generate access and refresh token pair."""
        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
