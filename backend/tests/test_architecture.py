"""Architecture, IDOR protection, and cascade cleanup test suite."""

import pytest
from bson import ObjectId
from app.db.cleanup import delete_deck_cascade, delete_notebook_cascade, delete_group_cascade
from app.db.migration import migrate_foreign_keys


def test_migration_idempotency(clean_db):
    """Verify that migrate_foreign_keys runs idempotently and safely."""
    u_id = ObjectId()
    d_id = clean_db.decks.insert_one({"title": "Migrate Test", "owner_id": str(u_id)}).inserted_id
    clean_db.cards.insert_one({"deck_id": str(d_id), "front": "Q", "back": "A"})

    # Run migration first time
    stats1 = migrate_foreign_keys(clean_db)
    assert stats1["decks_owner_id"] >= 1
    assert stats1["cards_deck_id"] >= 1

    deck = clean_db.decks.find_one({"_id": d_id})
    assert isinstance(deck["owner_id"], ObjectId)
    assert deck["owner_id"] == u_id

    # Run migration second time (should be idempotent with 0 changes)
    stats2 = migrate_foreign_keys(clean_db)
    assert stats2["decks_owner_id"] == 0
    assert stats2["cards_deck_id"] == 0


def test_delete_deck_cascade(clean_db):
    """Verify deck deletion cascades to cards and card reviews."""
    u_id = ObjectId()
    d_id = clean_db.decks.insert_one({"title": "Test Cascade", "owner_id": u_id}).inserted_id
    c_id = clean_db.cards.insert_one({"deck_id": d_id, "front": "Q1", "back": "A1"}).inserted_id
    clean_db.card_reviews.insert_one({"user_id": u_id, "card_id": c_id, "interval": 1})

    # Non-owner cannot delete
    assert not delete_deck_cascade(clean_db, str(d_id), str(ObjectId()))
    assert clean_db.decks.count_documents({"_id": d_id}) == 1

    # Owner can delete with cascade
    assert delete_deck_cascade(clean_db, str(d_id), str(u_id))
    assert clean_db.decks.count_documents({"_id": d_id}) == 0
    assert clean_db.cards.count_documents({"deck_id": d_id}) == 0
    assert clean_db.card_reviews.count_documents({"card_id": c_id}) == 0


def test_delete_notebook_cascade(clean_db):
    """Verify notebook deletion cascades to notes and quizzes."""
    u_id = ObjectId()
    nb_id = str(ObjectId())
    clean_db.notebooks.insert_one({"_id": nb_id, "owner_id": u_id, "title": "Math NB"})
    clean_db.notes.insert_one({"notebook_id": nb_id, "owner_id": u_id, "title": "Note 1"})
    clean_db.quizzes.insert_one({"notebook_id": nb_id, "owner_id": u_id, "title": "Quiz 1"})

    # Non-owner cannot delete
    assert not delete_notebook_cascade(clean_db, nb_id, str(ObjectId()))
    assert clean_db.notebooks.count_documents({"_id": nb_id}) == 1

    # Owner can delete
    assert delete_notebook_cascade(clean_db, nb_id, str(u_id))
    assert clean_db.notebooks.count_documents({"_id": nb_id}) == 0
    assert clean_db.notes.count_documents({"notebook_id": nb_id}) == 0
    assert clean_db.quizzes.count_documents({"notebook_id": nb_id}) == 0


def test_delete_group_cascade(clean_db):
    """Verify study group deletion cascades to members."""
    u_id = ObjectId()
    g_id = clean_db.study_groups.insert_one({"name": "Study Squad", "owner_id": u_id}).inserted_id
    clean_db.study_group_members.insert_one({"group_id": g_id, "user_id": u_id, "role": "owner"})

    # Non-owner cannot delete
    assert not delete_group_cascade(clean_db, str(g_id), str(ObjectId()))
    assert clean_db.study_groups.count_documents({"_id": g_id}) == 1

    # Owner deletes
    assert delete_group_cascade(clean_db, str(g_id), str(u_id))
    assert clean_db.study_groups.count_documents({"_id": g_id}) == 0
    assert clean_db.study_group_members.count_documents({"group_id": g_id}) == 0
