"""Pytest configuration and fixtures for testing."""

import pytest
import os
from pymongo import MongoClient

# Set test environment
os.environ.setdefault("MONGODB_DATABASE", "studysync_test")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-secret-key")


@pytest.fixture(scope="session")
def test_db():
    """Provide a test database connection. Skips if MongoDB is unavailable."""
    uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGODB_DATABASE", "studysync_test")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        db = client[db_name]
        yield db
        # Cleanup: drop test database
        client.drop_database(db_name)
        client.close()
    except Exception:
        pytest.skip("MongoDB is not available for integration tests")


@pytest.fixture
def clean_db(test_db):
    """Provide a clean database for each test."""
    for name in test_db.list_collection_names():
        test_db[name].delete_many({})
    yield test_db
