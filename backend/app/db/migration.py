"""Database migration script to normalize foreign keys and IDs to ObjectId."""

import logging
from bson import ObjectId
from pymongo.database import Database

logger = logging.getLogger(__name__)


def to_object_id_safe(val):
    """Return ObjectId if valid 24-char hex string, otherwise original val."""
    if isinstance(val, ObjectId):
        return val
    if isinstance(val, str) and len(val) == 24:
        try:
            return ObjectId(val)
        except Exception:
            return val
    return val


def migrate_foreign_keys(db: Database) -> dict:
    """Safely and idempotently convert string foreign keys to native ObjectId."""
    stats = {}

    # 1. Decks: owner_id
    decks_count = 0
    for doc in db.decks.find({"owner_id": {"$type": "string"}}):
        oid = to_object_id_safe(doc["owner_id"])
        if isinstance(oid, ObjectId):
            db.decks.update_one({"_id": doc["_id"]}, {"$set": {"owner_id": oid}})
            decks_count += 1
    stats["decks_owner_id"] = decks_count

    # 2. Cards: deck_id
    cards_count = 0
    for doc in db.cards.find({"deck_id": {"$type": "string"}}):
        oid = to_object_id_safe(doc["deck_id"])
        if isinstance(oid, ObjectId):
            db.cards.update_one({"_id": doc["_id"]}, {"$set": {"deck_id": oid}})
            cards_count += 1
    stats["cards_deck_id"] = cards_count

    # 3. Card reviews: user_id, card_id
    reviews_count = 0
    for doc in db.card_reviews.find({
        "$or": [
            {"user_id": {"$type": "string"}},
            {"card_id": {"$type": "string"}}
        ]
    }):
        updates = {}
        u_oid = to_object_id_safe(doc.get("user_id"))
        c_oid = to_object_id_safe(doc.get("card_id"))
        if isinstance(u_oid, ObjectId):
            updates["user_id"] = u_oid
        if isinstance(c_oid, ObjectId):
            updates["card_id"] = c_oid
        if updates:
            db.card_reviews.update_one({"_id": doc["_id"]}, {"$set": updates})
            reviews_count += 1
    stats["card_reviews"] = reviews_count

    # 4. Deck members: deck_id, user_id
    dm_count = 0
    for doc in db.deck_members.find({
        "$or": [
            {"deck_id": {"$type": "string"}},
            {"user_id": {"$type": "string"}}
        ]
    }):
        updates = {}
        d_oid = to_object_id_safe(doc.get("deck_id"))
        u_oid = to_object_id_safe(doc.get("user_id"))
        if isinstance(d_oid, ObjectId):
            updates["deck_id"] = d_oid
        if isinstance(u_oid, ObjectId):
            updates["user_id"] = u_oid
        if updates:
            db.deck_members.update_one({"_id": doc["_id"]}, {"$set": updates})
            dm_count += 1
    stats["deck_members"] = dm_count

    # 5. Study groups: owner_id
    sg_count = 0
    for doc in db.study_groups.find({"owner_id": {"$type": "string"}}):
        oid = to_object_id_safe(doc["owner_id"])
        if isinstance(oid, ObjectId):
            db.study_groups.update_one({"_id": doc["_id"]}, {"$set": {"owner_id": oid}})
            sg_count += 1
    stats["study_groups_owner_id"] = sg_count

    # 6. Study group members: group_id, user_id
    sgm_count = 0
    for doc in db.study_group_members.find({
        "$or": [
            {"group_id": {"$type": "string"}},
            {"user_id": {"$type": "string"}}
        ]
    }):
        updates = {}
        g_oid = to_object_id_safe(doc.get("group_id"))
        u_oid = to_object_id_safe(doc.get("user_id"))
        if isinstance(g_oid, ObjectId):
            updates["group_id"] = g_oid
        if isinstance(u_oid, ObjectId):
            updates["user_id"] = u_oid
        if updates:
            db.study_group_members.update_one({"_id": doc["_id"]}, {"$set": updates})
            sgm_count += 1
    stats["study_group_members"] = sgm_count

    # 7. Rooms: deck_id, created_by, group_id
    rooms_count = 0
    for doc in db.rooms.find({
        "$or": [
            {"deck_id": {"$type": "string"}},
            {"created_by": {"$type": "string"}},
            {"group_id": {"$type": "string"}}
        ]
    }):
        updates = {}
        d_oid = to_object_id_safe(doc.get("deck_id"))
        c_oid = to_object_id_safe(doc.get("created_by"))
        g_oid = to_object_id_safe(doc.get("group_id"))
        if isinstance(d_oid, ObjectId):
            updates["deck_id"] = d_oid
        if isinstance(c_oid, ObjectId):
            updates["created_by"] = c_oid
        if isinstance(g_oid, ObjectId):
            updates["group_id"] = g_oid
        if updates:
            db.rooms.update_one({"_id": doc["_id"]}, {"$set": updates})
            rooms_count += 1
    stats["rooms"] = rooms_count

    # 8. Room members: room_id, user_id
    rm_count = 0
    for doc in db.room_members.find({
        "$or": [
            {"room_id": {"$type": "string"}},
            {"user_id": {"$type": "string"}}
        ]
    }):
        updates = {}
        r_oid = to_object_id_safe(doc.get("room_id"))
        u_oid = to_object_id_safe(doc.get("user_id"))
        if isinstance(r_oid, ObjectId):
            updates["room_id"] = r_oid
        if isinstance(u_oid, ObjectId):
            updates["user_id"] = u_oid
        if updates:
            db.room_members.update_one({"_id": doc["_id"]}, {"$set": updates})
            rm_count += 1
    stats["room_members"] = rm_count

    # 9. Room messages: room_id, user_id
    rmsg_count = 0
    for doc in db.room_messages.find({
        "$or": [
            {"room_id": {"$type": "string"}},
            {"user_id": {"$type": "string"}}
        ]
    }):
        updates = {}
        r_oid = to_object_id_safe(doc.get("room_id"))
        u_oid = to_object_id_safe(doc.get("user_id"))
        if isinstance(r_oid, ObjectId):
            updates["room_id"] = r_oid
        if isinstance(u_oid, ObjectId):
            updates["user_id"] = u_oid
        if updates:
            db.room_messages.update_one({"_id": doc["_id"]}, {"$set": updates})
            rmsg_count += 1
    stats["room_messages"] = rmsg_count

    # 10. Study sessions: user_id, deck_id
    ss_count = 0
    for doc in db.study_sessions.find({
        "$or": [
            {"user_id": {"$type": "string"}},
            {"deck_id": {"$type": "string"}}
        ]
    }):
        updates = {}
        u_oid = to_object_id_safe(doc.get("user_id"))
        d_oid = to_object_id_safe(doc.get("deck_id"))
        if isinstance(u_oid, ObjectId):
            updates["user_id"] = u_oid
        if isinstance(d_oid, ObjectId):
            updates["deck_id"] = d_oid
        if updates:
            db.study_sessions.update_one({"_id": doc["_id"]}, {"$set": updates})
            ss_count += 1
    stats["study_sessions"] = ss_count

    # 11. Documents: owner_id
    doc_count = 0
    for doc in db.documents.find({"owner_id": {"$type": "string"}}):
        oid = to_object_id_safe(doc["owner_id"])
        if isinstance(oid, ObjectId):
            db.documents.update_one({"_id": doc["_id"]}, {"$set": {"owner_id": oid}})
            doc_count += 1
    stats["documents_owner_id"] = doc_count

    # 12. Notebooks: owner_id, documents list
    nb_count = 0
    for doc in db.notebooks.find():
        updates = {}
        if isinstance(doc.get("owner_id"), str) and len(doc["owner_id"]) == 24:
            oid = to_object_id_safe(doc["owner_id"])
            if isinstance(oid, ObjectId):
                updates["owner_id"] = oid
        docs_list = doc.get("documents", [])
        if any(isinstance(d, str) and len(d) == 24 for d in docs_list):
            updates["documents"] = [to_object_id_safe(d) for d in docs_list]
        if updates:
            db.notebooks.update_one({"_id": doc["_id"]}, {"$set": updates})
            nb_count += 1
    stats["notebooks"] = nb_count

    # 13. Notes: owner_id, notebook_id
    notes_count = 0
    for doc in db.notes.find({
        "$or": [
            {"owner_id": {"$type": "string"}},
            {"notebook_id": {"$type": "string"}}
        ]
    }):
        updates = {}
        u_oid = to_object_id_safe(doc.get("owner_id"))
        n_oid = to_object_id_safe(doc.get("notebook_id"))
        if isinstance(u_oid, ObjectId):
            updates["owner_id"] = u_oid
        if isinstance(n_oid, ObjectId):
            updates["notebook_id"] = n_oid
        if updates:
            db.notes.update_one({"_id": doc["_id"]}, {"$set": updates})
            notes_count += 1
    stats["notes"] = notes_count

    # 14. AI Conversations: owner_id, notebook_id
    conv_count = 0
    for doc in db.ai_conversations.find({
        "$or": [
            {"owner_id": {"$type": "string"}},
            {"notebook_id": {"$type": "string"}}
        ]
    }):
        updates = {}
        u_oid = to_object_id_safe(doc.get("owner_id"))
        n_oid = to_object_id_safe(doc.get("notebook_id"))
        if isinstance(u_oid, ObjectId):
            updates["owner_id"] = u_oid
        if isinstance(n_oid, ObjectId):
            updates["notebook_id"] = n_oid
        if updates:
            db.ai_conversations.update_one({"_id": doc["_id"]}, {"$set": updates})
            conv_count += 1
    stats["ai_conversations"] = conv_count

    logger.info(f"Database migration completed: {stats}")
    return stats


if __name__ == "__main__":
    from app.db.mongodb import get_database, connect_to_mongodb
    connect_to_mongodb()
    database = get_database()
    result = migrate_foreign_keys(database)
    print("Migration finished:", result)
