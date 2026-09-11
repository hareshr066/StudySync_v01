"""Global search API."""
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.db.mongodb import get_database
import re

router = APIRouter(prefix="/api/v1/search", tags=["search"])

@router.get("")
def global_search(
    q: str = Query(..., min_length=1, max_length=200),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    db = get_database()
    owner_id = current_user["_id"]
    query_regex = re.compile(re.escape(q.strip()), re.IGNORECASE)
    results = {"notebooks": [], "documents": [], "decks": [], "notes": []}
    
    # Search notebooks
    nbs = list(db.notebooks.find({"owner_id": owner_id, "title": query_regex}, {"title": 1, "description": 1, "updated_at": 1}).limit(5))
    results["notebooks"] = [{"id": n["_id"], "title": n["title"], "description": n.get("description", ""), "type": "notebook"} for n in nbs]
    
    # Search documents
    docs = list(db.documents.find({"owner_id": owner_id, "title": query_regex}, {"title": 1, "mime_type": 1, "status": 1}).limit(5))
    results["documents"] = [{"id": d["_id"], "title": d["title"], "status": d.get("status", "ready"), "type": "document"} for d in docs]
    
    # Search decks (owner or member)
    memberships = list(db.deck_members.find({"user_id": owner_id}))
    deck_ids = [ObjectId(m["deck_id"]) for m in memberships if ObjectId.is_valid(m["deck_id"])]
    if deck_ids:
        decks = list(db.decks.find({"_id": {"$in": deck_ids}, "$or": [{"title": query_regex}, {"description": query_regex}]}, {"title": 1, "description": 1, "card_count": 1}).limit(5))
        results["decks"] = [{"id": str(d["_id"]), "title": d["title"], "description": d.get("description", ""), "card_count": d.get("card_count", 0), "type": "deck"} for d in decks]
    
    # Search notes
    notes = list(db.notes.find({"owner_id": owner_id, "title": query_regex}, {"title": 1, "updated_at": 1}).limit(5))
    results["notes"] = [{"id": n["_id"], "title": n["title"], "type": "note"} for n in notes]
    
    total = sum(len(v) for v in results.values())
    return {"results": results, "total": total, "query": q}
