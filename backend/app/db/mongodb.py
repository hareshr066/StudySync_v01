"""MongoDB connection management."""

from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional

from app.core.config import settings

_client: Optional[MongoClient] = None
_database: Optional[Database] = None


def connect_to_mongodb() -> None:
    """Establish MongoDB connection."""
    global _client, _database
    _client = MongoClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000
    )
    _database = _client[settings.MONGODB_DATABASE]
    # Test connection
    _client.admin.command("ping")
    print(f"[OK] Connected to MongoDB database: {settings.MONGODB_DATABASE}")


def close_mongodb_connection() -> None:
    """Close MongoDB connection."""
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None
        print("[OK] MongoDB connection closed")


def get_database() -> Database:
    """Get the MongoDB database instance."""
    if _database is None:
        raise RuntimeError("MongoDB is not connected. Call connect_to_mongodb() first.")
    return _database


def get_client() -> MongoClient:
    """Get the MongoDB client instance."""
    if _client is None:
        raise RuntimeError("MongoDB is not connected. Call connect_to_mongodb() first.")
    return _client
