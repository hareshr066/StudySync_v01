"""Cascading delete and resource cleanup helpers."""

import logging
from bson import ObjectId
from pymongo.database import Database

logger = logging.getLogger(__name__)


def to_object_id(val):
    """Safely convert value to ObjectId if possible."""
    if isinstance(val, ObjectId):
        return val
    try:
        return ObjectId(str(val))
    except Exception:
        return val


def delete_deck_cascade(db: Database, deck_id: str, owner_id: str) -> bool:
    """Delete a deck and all related cards, reviews, memberships, and room references."""
    d_oid = to_object_id(deck_id)
    u_oid = to_object_id(owner_id)

    # Verify ownership
    deck = db.decks.find_one({"_id": d_oid, "owner_id": {"$in": [u_oid, str(u_oid)]}})
    if not deck:
        return False

    # 1. Find all card IDs in this deck
    cards = list(db.cards.find({"deck_id": {"$in": [d_oid, str(d_oid)]}}, {"_id": 1}))
    card_ids = [c["_id"] for c in cards]
    card_str_ids = [str(c["_id"]) for c in cards]
    all_card_ids = list(set(card_ids + card_str_ids))

    # 2. Delete card reviews
    if all_card_ids:
        db.card_reviews.delete_many({"card_id": {"$in": all_card_ids}})

    # 3. Delete cards
    db.cards.delete_many({"deck_id": {"$in": [d_oid, str(d_oid)]}})

    # 4. Delete deck memberships
    db.deck_members.delete_many({"deck_id": {"$in": [d_oid, str(d_oid)]}})

    # 5. Clean up rooms referencing this deck
    db.rooms.update_many(
        {"deck_id": {"$in": [d_oid, str(d_oid)]}},
        {"$set": {"deck_id": None, "status": "ended"}}
    )

    # 6. Delete deck itself
    res = db.decks.delete_one({"_id": d_oid})
    logger.info(f"Cascaded deletion for deck {deck_id}: deleted {len(card_ids)} cards")
    return res.deleted_count > 0


def delete_notebook_cascade(db: Database, notebook_id: str, owner_id: str) -> bool:
    """Delete a notebook and all associated notes and conversation history."""
    nb_oid = to_object_id(notebook_id)
    u_oid = to_object_id(owner_id)

    notebook = db.notebooks.find_one({
        "_id": {"$in": [nb_oid, str(nb_oid)]},
        "owner_id": {"$in": [u_oid, str(u_oid)]}
    })
    if not notebook:
        return False

    # 1. Delete notes belonging to this notebook
    db.notes.delete_many({"notebook_id": {"$in": [nb_oid, str(nb_oid)]}})

    # 2. Delete AI conversations for this notebook
    db.ai_conversations.delete_many({"notebook_id": {"$in": [nb_oid, str(nb_oid)]}})

    # 3. Delete quizzes for this notebook
    db.quizzes.delete_many({"notebook_id": {"$in": [nb_oid, str(nb_oid)]}})

    # 4. Delete notebook itself
    res = db.notebooks.delete_one({"_id": {"$in": [nb_oid, str(nb_oid)]}})
    logger.info(f"Cascaded deletion for notebook {notebook_id}")
    return res.deleted_count > 0


def delete_document_cascade(db: Database, doc_id: str, owner_id: str) -> bool:
    """Detach document from all notebooks and delete document record."""
    d_oid = to_object_id(doc_id)
    u_oid = to_object_id(owner_id)

    doc = db.documents.find_one({
        "_id": {"$in": [d_oid, str(d_oid)]},
        "owner_id": {"$in": [u_oid, str(u_oid)]}
    })
    if not doc:
        return False

    # 1. Pull document reference from all notebooks
    db.notebooks.update_many(
        {"documents": {"$in": [d_oid, str(d_oid)]}},
        {"$pull": {"documents": {"$in": [d_oid, str(d_oid)]}}}
    )

    # 2. Delete document record
    res = db.documents.delete_one({"_id": {"$in": [d_oid, str(d_oid)]}})
    logger.info(f"Cascaded deletion for document {doc_id}")
    return res.deleted_count > 0


def delete_group_cascade(db: Database, group_id: str, owner_id: str) -> bool:
    """Delete a study group and clean up memberships and associated group rooms."""
    g_oid = to_object_id(group_id)
    u_oid = to_object_id(owner_id)

    group = db.study_groups.find_one({
        "_id": g_oid,
        "owner_id": {"$in": [u_oid, str(u_oid)]}
    })
    if not group:
        return False

    # 1. Delete group members
    db.study_group_members.delete_many({"group_id": {"$in": [g_oid, str(g_oid)]}})

    # 2. Clean up rooms linked to group
    db.rooms.update_many(
        {"group_id": {"$in": [g_oid, str(g_oid)]}},
        {"$set": {"status": "ended"}}
    )

    # 3. Delete group
    res = db.study_groups.delete_one({"_id": g_oid})
    logger.info(f"Cascaded deletion for study group {group_id}")
    return res.deleted_count > 0
