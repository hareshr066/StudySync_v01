"""Integration tests for the API using the FastAPI test client."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_client(clean_db, monkeypatch):
    """Create a test client with a clean database."""
    # Patch the database connection to use our test db
    import app.db.mongodb as mongodb_mod
    monkeypatch.setattr(mongodb_mod, "_database", clean_db)
    monkeypatch.setattr(mongodb_mod, "_client", clean_db.client)

    from app.db.indexes import create_indexes
    create_indexes(clean_db)

    from app.main import app
    client = TestClient(app)
    yield client


@pytest.fixture
def auth_headers(app_client):
    """Register a user and return auth headers."""
    res = app_client.post("/api/v1/auth/register", json={
        "name": "Test User", "email": "test@example.com", "password": "testpassword123"
    })
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_headers(app_client):
    """Register a second user and return auth headers."""
    res = app_client.post("/api/v1/auth/register", json={
        "name": "Second User", "email": "second@example.com", "password": "testpassword123"
    })
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# === AUTH TESTS ===

class TestAuth:
    def test_register(self, app_client):
        res = app_client.post("/api/v1/auth/register", json={
            "name": "New User", "email": "new@example.com", "password": "password123"
        })
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_duplicate_email(self, app_client):
        app_client.post("/api/v1/auth/register", json={
            "name": "User A", "email": "dup@example.com", "password": "password123"
        })
        res = app_client.post("/api/v1/auth/register", json={
            "name": "User B", "email": "dup@example.com", "password": "password123"
        })
        assert res.status_code == 409

    def test_login(self, app_client, auth_headers):
        res = app_client.post("/api/v1/auth/login", json={
            "email": "test@example.com", "password": "testpassword123"
        })
        assert res.status_code == 200
        assert "access_token" in res.json()

    def test_invalid_password(self, app_client, auth_headers):
        res = app_client.post("/api/v1/auth/login", json={
            "email": "test@example.com", "password": "wrongpassword"
        })
        assert res.status_code == 401

    def test_me(self, app_client, auth_headers):
        res = app_client.get("/api/v1/auth/me", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    def test_protected_no_token(self, app_client):
        res = app_client.get("/api/v1/auth/me")
        assert res.status_code in (401, 403)

    def test_refresh_token(self, app_client):
        reg = app_client.post("/api/v1/auth/register", json={
            "name": "Refresh User", "email": "refresh@example.com", "password": "password123"
        })
        refresh = reg.json()["refresh_token"]
        res = app_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert res.status_code == 200
        assert "access_token" in res.json()


# === DECK TESTS ===

class TestDecks:
    def test_create_deck(self, app_client, auth_headers):
        res = app_client.post("/api/v1/decks", json={"title": "Test Deck", "description": "A test deck"}, headers=auth_headers)
        assert res.status_code == 201
        assert res.json()["title"] == "Test Deck"

    def test_list_decks(self, app_client, auth_headers):
        app_client.post("/api/v1/decks", json={"title": "Deck 1"}, headers=auth_headers)
        res = app_client.get("/api/v1/decks", headers=auth_headers)
        assert res.status_code == 200
        assert len(res.json()["decks"]) >= 1

    def test_get_deck(self, app_client, auth_headers):
        create = app_client.post("/api/v1/decks", json={"title": "Get Me"}, headers=auth_headers)
        deck_id = create.json()["id"]
        res = app_client.get(f"/api/v1/decks/{deck_id}", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["title"] == "Get Me"

    def test_update_deck(self, app_client, auth_headers):
        create = app_client.post("/api/v1/decks", json={"title": "Old Title"}, headers=auth_headers)
        deck_id = create.json()["id"]
        res = app_client.patch(f"/api/v1/decks/{deck_id}", json={"title": "New Title"}, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["title"] == "New Title"

    def test_delete_deck(self, app_client, auth_headers):
        create = app_client.post("/api/v1/decks", json={"title": "Delete Me"}, headers=auth_headers)
        deck_id = create.json()["id"]
        res = app_client.delete(f"/api/v1/decks/{deck_id}", headers=auth_headers)
        assert res.status_code == 204

    def test_unauthorized_access(self, app_client, auth_headers, second_user_headers):
        create = app_client.post("/api/v1/decks", json={"title": "Private Deck"}, headers=auth_headers)
        deck_id = create.json()["id"]
        res = app_client.get(f"/api/v1/decks/{deck_id}", headers=second_user_headers)
        assert res.status_code == 403


# === CARD TESTS ===

class TestCards:
    def _create_deck(self, client, headers):
        res = client.post("/api/v1/decks", json={"title": "Card Deck"}, headers=headers)
        return res.json()["id"]

    def test_create_card(self, app_client, auth_headers):
        deck_id = self._create_deck(app_client, auth_headers)
        res = app_client.post(f"/api/v1/decks/{deck_id}/cards", json={"front": "Q?", "back": "A!"}, headers=auth_headers)
        assert res.status_code == 201

    def test_list_cards(self, app_client, auth_headers):
        deck_id = self._create_deck(app_client, auth_headers)
        app_client.post(f"/api/v1/decks/{deck_id}/cards", json={"front": "Q1", "back": "A1"}, headers=auth_headers)
        res = app_client.get(f"/api/v1/decks/{deck_id}/cards", headers=auth_headers)
        assert res.status_code == 200
        assert len(res.json()["cards"]) >= 1

    def test_delete_card(self, app_client, auth_headers):
        deck_id = self._create_deck(app_client, auth_headers)
        create = app_client.post(f"/api/v1/decks/{deck_id}/cards", json={"front": "Del", "back": "Me"}, headers=auth_headers)
        card_id = create.json()["id"]
        res = app_client.delete(f"/api/v1/cards/{card_id}", headers=auth_headers)
        assert res.status_code == 204

    def test_unauthorized_card_access(self, app_client, auth_headers, second_user_headers):
        deck_id = self._create_deck(app_client, auth_headers)
        res = app_client.get(f"/api/v1/decks/{deck_id}/cards", headers=second_user_headers)
        assert res.status_code == 403


# === SHARING TESTS ===

class TestSharing:
    def test_share_and_join(self, app_client, auth_headers, second_user_headers):
        # Create a deck
        create = app_client.post("/api/v1/decks", json={"title": "Shared Deck"}, headers=auth_headers)
        deck_id = create.json()["id"]

        # Generate share token
        share = app_client.post(f"/api/v1/decks/{deck_id}/share", headers=auth_headers)
        assert share.status_code == 200
        token = share.json()["share_token"]

        # Join with second user
        join = app_client.post(f"/api/v1/decks/join/{token}", headers=second_user_headers)
        assert join.status_code == 200

        # Second user can now access
        access = app_client.get(f"/api/v1/decks/{deck_id}", headers=second_user_headers)
        assert access.status_code == 200

    def test_duplicate_join(self, app_client, auth_headers, second_user_headers):
        create = app_client.post("/api/v1/decks", json={"title": "Dup Join Deck"}, headers=auth_headers)
        deck_id = create.json()["id"]
        share = app_client.post(f"/api/v1/decks/{deck_id}/share", headers=auth_headers)
        token = share.json()["share_token"]

        app_client.post(f"/api/v1/decks/join/{token}", headers=second_user_headers)
        # Second join should succeed (idempotent)
        res = app_client.post(f"/api/v1/decks/join/{token}", headers=second_user_headers)
        assert res.status_code == 200


# === STUDY TESTS ===

class TestStudy:
    def _setup_deck_with_card(self, client, headers):
        deck = client.post("/api/v1/decks", json={"title": "Study Deck"}, headers=headers)
        deck_id = deck.json()["id"]
        card = client.post(f"/api/v1/decks/{deck_id}/cards", json={"front": "What is BFS?", "back": "Breadth First Search"}, headers=headers)
        return deck_id, card.json()["id"]

    def test_get_next_card(self, app_client, auth_headers):
        deck_id, _ = self._setup_deck_with_card(app_client, auth_headers)
        res = app_client.get(f"/api/v1/study/{deck_id}/next", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["front"] == "What is BFS?"
        assert res.json()["is_new"] is True

    def test_submit_review_good(self, app_client, auth_headers):
        deck_id, card_id = self._setup_deck_with_card(app_client, auth_headers)
        res = app_client.post("/api/v1/study/review", json={
            "card_id": card_id, "deck_id": deck_id, "rating": "good"
        }, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["repetitions"] == 1
        assert res.json()["interval"] == 1.0

    def test_submit_review_again(self, app_client, auth_headers):
        deck_id, card_id = self._setup_deck_with_card(app_client, auth_headers)
        # First review good
        app_client.post("/api/v1/study/review", json={
            "card_id": card_id, "deck_id": deck_id, "rating": "good"
        }, headers=auth_headers)
        # Then again
        res = app_client.post("/api/v1/study/review", json={
            "card_id": card_id, "deck_id": deck_id, "rating": "again"
        }, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["repetitions"] == 0

    def test_deck_stats(self, app_client, auth_headers):
        deck_id, _ = self._setup_deck_with_card(app_client, auth_headers)
        res = app_client.get(f"/api/v1/study/{deck_id}/stats", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["total_cards"] == 1


# === ROOM TESTS ===

class TestRooms:
    def _create_deck(self, client, headers):
        res = client.post("/api/v1/decks", json={"title": "Room Deck"}, headers=headers)
        return res.json()["id"]

    def test_create_room(self, app_client, auth_headers):
        deck_id = self._create_deck(app_client, auth_headers)
        res = app_client.post("/api/v1/rooms", json={"deck_id": deck_id, "name": "Study Room"}, headers=auth_headers)
        assert res.status_code == 201
        assert res.json()["name"] == "Study Room"

    def test_join_room(self, app_client, auth_headers, second_user_headers):
        deck_id = self._create_deck(app_client, auth_headers)
        # Share deck with second user
        share = app_client.post(f"/api/v1/decks/{deck_id}/share", headers=auth_headers)
        token = share.json()["share_token"]
        app_client.post(f"/api/v1/decks/join/{token}", headers=second_user_headers)

        room = app_client.post("/api/v1/rooms", json={"deck_id": deck_id, "name": "Join Room"}, headers=auth_headers)
        room_id = room.json()["id"]
        res = app_client.post(f"/api/v1/rooms/{room_id}/join", headers=second_user_headers)
        assert res.status_code == 200

    def test_leave_room(self, app_client, auth_headers):
        deck_id = self._create_deck(app_client, auth_headers)
        room = app_client.post("/api/v1/rooms", json={"deck_id": deck_id, "name": "Leave Room"}, headers=auth_headers)
        room_id = room.json()["id"]
        res = app_client.post(f"/api/v1/rooms/{room_id}/leave", headers=auth_headers)
        assert res.status_code == 200

    def test_get_room(self, app_client, auth_headers):
        deck_id = self._create_deck(app_client, auth_headers)
        room = app_client.post("/api/v1/rooms", json={"deck_id": deck_id, "name": "Get Room"}, headers=auth_headers)
        room_id = room.json()["id"]
        res = app_client.get(f"/api/v1/rooms/{room_id}", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["room"]["name"] == "Get Room"
