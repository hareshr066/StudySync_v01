from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.schemas.notes import NoteCreate, NoteUpdate, NoteResponse, NoteInDB
from app.db.mongodb import get_database

router = APIRouter(prefix="/api/v1/notes", tags=["notes"])

@router.post("", response_model=NoteResponse)
def create_note(note: NoteCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    new_note = NoteInDB(
        _id=str(ObjectId()),
        owner_id=current_user["_id"],
        title=note.title,
        content=note.content,
        tags=note.tags,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.notes.insert_one(new_note.model_dump(by_alias=True))
    return new_note

@router.get("", response_model=dict)
def list_notes(skip: int = 0, limit: int = 50, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    notes = list(db.notes.find({"owner_id": current_user["_id"]}).sort("updated_at", -1).skip(skip).limit(limit))
    return {"notes": [NoteInDB(**n) for n in notes], "total": len(notes)}

@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    note = db.notes.find_one({"_id": note_id, "owner_id": current_user["_id"]})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteInDB(**note)

@router.patch("/{note_id}", response_model=NoteResponse)
def update_note(note_id: str, note_update: NoteUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    update_data = {k: v for k, v in note_update.model_dump(exclude_unset=True).items()}
    if not update_data:
        return get_note(note_id, current_user)
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    res = db.notes.update_one({"_id": note_id, "owner_id": current_user["_id"]}, {"$set": update_data})
    
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
        
    return get_note(note_id, current_user)

@router.delete("/{note_id}")
def delete_note(note_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    res = db.notes.delete_one({"_id": note_id, "owner_id": current_user["_id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"status": "success"}
