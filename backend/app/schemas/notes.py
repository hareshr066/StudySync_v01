from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class NoteBase(BaseModel):
    title: str = Field(..., description="Note title")
    content: Optional[Dict[str, Any]] = None # Structured blocks content
    tags: List[str] = []

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class NoteInDB(NoteBase):
    id: str = Field(alias="_id")
    owner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class NoteResponse(NoteInDB):
    pass
