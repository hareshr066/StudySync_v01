"""Database index creation for all collections."""

from pymongo import ASCENDING
from pymongo.database import Database


def create_indexes(db: Database) -> None:
    """Create all required indexes. Safe to call on startup — MongoDB skips existing indexes."""

    # users: unique email
    db.users.create_index(
        [("email", ASCENDING)],
        unique=True,
        name="idx_users_email_unique",
    )

    # decks: owner lookup
    db.decks.create_index(
        [("owner_id", ASCENDING)],
        name="idx_decks_owner_id",
    )

    # cards: deck lookup
    db.cards.create_index(
        [("deck_id", ASCENDING)],
        name="idx_cards_deck_id",
    )
    db.cards.create_index(
        [("deck_id", ASCENDING), ("created_at", ASCENDING)],
        name="idx_cards_deck_id_created_at",
    )

    # deck_members: unique membership, user lookup
    db.deck_members.create_index(
        [("deck_id", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="idx_deck_members_deck_user_unique",
    )
    db.deck_members.create_index(
        [("user_id", ASCENDING)],
        name="idx_deck_members_user_id",
    )

    # card_reviews: unique user+card review state, due date lookup
    db.card_reviews.create_index(
        [("user_id", ASCENDING), ("card_id", ASCENDING)],
        unique=True,
        name="idx_card_reviews_user_card_unique",
    )
    db.card_reviews.create_index(
        [("user_id", ASCENDING), ("due_at", ASCENDING)],
        name="idx_card_reviews_user_due_at",
    )

    # rooms: deck and status lookup
    db.rooms.create_index(
        [("deck_id", ASCENDING)],
        name="idx_rooms_deck_id",
    )
    db.rooms.create_index(
        [("status", ASCENDING)],
        name="idx_rooms_status",
    )

    # room_members: unique membership
    db.room_members.create_index(
        [("room_id", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="idx_room_members_room_user_unique",
    )

    # decks: share_token lookup
    db.decks.create_index(
        [("share_token", ASCENDING)],
        name="idx_decks_share_token",
        sparse=True,
    )

    # study_groups: owner lookup
    db.study_groups.create_index([("owner_id", ASCENDING)], name="idx_study_groups_owner_id")
    db.study_groups.create_index([("invite_token", ASCENDING)], name="idx_study_groups_invite_token", sparse=True)

    # study_group_members: unique membership
    db.study_group_members.create_index(
        [("group_id", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="idx_group_members_unique"
    )

    # study_sessions
    db.study_sessions.create_index([("user_id", ASCENDING), ("started_at", ASCENDING)], name="idx_study_sessions_user_started")

    # notifications
    db.notifications.create_index([("user_id", ASCENDING), ("read", ASCENDING), ("created_at", ASCENDING)], name="idx_notifications_user_read")

    # room_messages
    db.room_messages.create_index([("room_id", ASCENDING), ("created_at", ASCENDING)], name="idx_room_messages_room_created")

    # ai_conversations
    db.ai_conversations.create_index([("owner_id", ASCENDING), ("updated_at", ASCENDING)], name="idx_conversations_owner_updated")
    db.ai_conversations.create_index([("notebook_id", ASCENDING)], name="idx_conversations_notebook_id", sparse=True)

    # documents
    db.documents.create_index([("owner_id", ASCENDING), ("created_at", ASCENDING)], name="idx_documents_owner_created")
    db.documents.create_index([("owner_id", ASCENDING), ("status", ASCENDING)], name="idx_documents_owner_status")

    # notebooks
    db.notebooks.create_index([("owner_id", ASCENDING), ("updated_at", ASCENDING)], name="idx_notebooks_owner_updated")
    db.notebooks.create_index([("owner_id", ASCENDING), ("created_at", ASCENDING)], name="idx_notebooks_owner_created")

    # notes
    db.notes.create_index([("owner_id", ASCENDING), ("notebook_id", ASCENDING), ("updated_at", ASCENDING)], name="idx_notes_owner_notebook_updated")

    # quizzes and attempts
    db.quizzes.create_index([("owner_id", ASCENDING), ("created_at", ASCENDING)], name="idx_quizzes_owner_created")
    db.quizzes.create_index([("owner_id", ASCENDING), ("notebook_id", ASCENDING)], name="idx_quizzes_owner_notebook", sparse=True)
    db.quiz_attempts.create_index([("user_id", ASCENDING), ("quiz_id", ASCENDING), ("created_at", ASCENDING)], name="idx_quiz_attempts_user_quiz")

    # study_plans
    db.study_plans.create_index([("owner_id", ASCENDING), ("created_at", ASCENDING)], name="idx_study_plans_owner_created")

    print("[OK] Database indexes created/verified")
