from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.schemas.notebooks import NotebookCreate, NotebookUpdate, NotebookResponse, NotebookInDB
from app.db.mongodb import get_database

router = APIRouter(prefix="/api/v1/notebooks", tags=["notebooks"])

def _u_refs(user_id: str) -> List[Any]:
    refs = [user_id]
    if len(str(user_id)) == 24:
        try:
            refs.append(ObjectId(str(user_id)))
        except Exception:
            pass
    return refs

def _sanitize_nb(nb: dict) -> dict:
    nb["_id"] = str(nb["_id"])
    nb["owner_id"] = str(nb["owner_id"])
    nb["documents"] = [str(d) for d in nb.get("documents", [])]
    nb["notes"] = [str(n) for n in nb.get("notes", [])]
    return nb

@router.post("", response_model=NotebookResponse)
def create_notebook(nb: NotebookCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    new_nb = NotebookInDB(
        _id=str(ObjectId()),
        owner_id=str(current_user["_id"]),
        title=nb.title,
        description=nb.description,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.notebooks.insert_one(new_nb.model_dump(by_alias=True))
    return new_nb

@router.get("", response_model=dict)
def list_notebooks(skip: int = 0, limit: int = 50, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    u_refs = _u_refs(current_user["_id"])
    nbs = list(db.notebooks.find({"owner_id": {"$in": u_refs}}).sort("updated_at", -1).skip(skip).limit(limit))
    return {"notebooks": [NotebookInDB(**_sanitize_nb(n)) for n in nbs], "total": len(nbs)}

@router.get("/{nb_id}", response_model=NotebookResponse)
def get_notebook(nb_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    u_refs = _u_refs(current_user["_id"])
    nb_refs = [nb_id]
    if len(str(nb_id)) == 24:
        try:
            nb_refs.append(ObjectId(str(nb_id)))
        except Exception:
            pass
    nb = db.notebooks.find_one({"_id": {"$in": nb_refs}, "owner_id": {"$in": u_refs}})
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return NotebookInDB(**_sanitize_nb(nb))

@router.patch("/{nb_id}", response_model=NotebookResponse)
def update_notebook(nb_id: str, nb_update: NotebookUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    u_refs = _u_refs(current_user["_id"])
    nb_refs = [nb_id]
    if len(str(nb_id)) == 24:
        try:
            nb_refs.append(ObjectId(str(nb_id)))
        except Exception:
            pass
    update_data = {k: v for k, v in nb_update.model_dump(exclude_unset=True).items()}
    if not update_data:
        return get_notebook(nb_id, current_user)
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    res = db.notebooks.update_many({"_id": {"$in": nb_refs}, "owner_id": {"$in": u_refs}}, {"$set": update_data})
    
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notebook not found")
        
    return get_notebook(nb_id, current_user)

@router.delete("/{nb_id}")
def delete_notebook(nb_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    from app.db.cleanup import delete_notebook_cascade
    success = delete_notebook_cascade(db, nb_id, current_user["_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return {"status": "success"}

@router.post("/{nb_id}/documents/{doc_id}")
def add_document_to_notebook(nb_id: str, doc_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    u_refs = _u_refs(current_user["_id"])
    d_refs = [doc_id]
    if len(str(doc_id)) == 24:
        try:
            d_refs.append(ObjectId(str(doc_id)))
        except Exception:
            pass
    # Verify document ownership
    doc = db.documents.find_one({"_id": {"$in": d_refs}, "owner_id": {"$in": u_refs}})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    nb_refs = [nb_id]
    if len(str(nb_id)) == 24:
        try:
            nb_refs.append(ObjectId(str(nb_id)))
        except Exception:
            pass

    res = db.notebooks.update_many(
        {"_id": {"$in": nb_refs}, "owner_id": {"$in": u_refs}},
        {"$addToSet": {"documents": str(doc["_id"])}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return get_notebook(nb_id, current_user)

@router.delete("/{nb_id}/documents/{doc_id}")
def remove_document_from_notebook(nb_id: str, doc_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    u_refs = _u_refs(current_user["_id"])
    nb_refs = [nb_id]
    if len(str(nb_id)) == 24:
        try:
            nb_refs.append(ObjectId(str(nb_id)))
        except Exception:
            pass

    d_pull = [doc_id]
    if len(str(doc_id)) == 24:
        try:
            d_pull.append(ObjectId(str(doc_id)))
        except Exception:
            pass

    res = db.notebooks.update_many(
        {"_id": {"$in": nb_refs}, "owner_id": {"$in": u_refs}},
        {"$pull": {"documents": {"$in": d_pull}}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return get_notebook(nb_id, current_user)

@router.get("/{nb_id}/notes")
def get_notebook_notes(nb_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    u_refs = _u_refs(current_user["_id"])
    nb_refs = [nb_id]
    if len(str(nb_id)) == 24:
        try:
            nb_refs.append(ObjectId(str(nb_id)))
        except Exception:
            pass
    nb = db.notebooks.find_one({"_id": {"$in": nb_refs}, "owner_id": {"$in": u_refs}})
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    note_ids = nb.get("notes", [])
    if not note_ids:
        return {"notes": [], "total": 0}
    
    n_query_ids = []
    for nid in note_ids:
        n_query_ids.append(nid)
        if isinstance(nid, str) and len(nid) == 24:
            try:
                n_query_ids.append(ObjectId(nid))
            except Exception:
                pass
        elif isinstance(nid, ObjectId):
            n_query_ids.append(str(nid))

    from app.schemas.notes import NoteInDB
    notes = list(db.notes.find({"_id": {"$in": n_query_ids}, "owner_id": {"$in": u_refs}}).sort("updated_at", -1))
    sanitized = []
    for n in notes:
        n["_id"] = str(n["_id"])
        n["owner_id"] = str(n["owner_id"])
        sanitized.append(NoteInDB(**n))
    return {"notes": sanitized, "total": len(sanitized)}

@router.post("/{nb_id}/notes")
def create_notebook_note(nb_id: str, note: dict, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    u_refs = _u_refs(current_user["_id"])
    nb_refs = [nb_id]
    if len(str(nb_id)) == 24:
        try:
            nb_refs.append(ObjectId(str(nb_id)))
        except Exception:
            pass
    nb = db.notebooks.find_one({"_id": {"$in": nb_refs}, "owner_id": {"$in": u_refs}})
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    from app.schemas.notes import NoteInDB
    now = datetime.now(timezone.utc)
    new_note = NoteInDB(
        _id=str(ObjectId()),
        owner_id=str(current_user["_id"]),
        title=note.get("title", "Untitled Note"),
        content=note.get("content", {}),
        tags=note.get("tags", []),
        created_at=now,
        updated_at=now
    )
    db.notes.insert_one(new_note.model_dump(by_alias=True))
    db.notebooks.update_many(
        {"_id": {"$in": nb_refs}},
        {"$addToSet": {"notes": new_note.id}, "$set": {"updated_at": now}}
    )
    return new_note
