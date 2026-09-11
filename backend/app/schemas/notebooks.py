from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NotebookBase(BaseModel):
    title: str = Field(..., description="Notebook title")
    description: Optional[str] = None

class NotebookCreate(NotebookBase):
    pass

class NotebookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class NotebookInDB(NotebookBase):
    id: str = Field(alias="_id")
    owner_id: str
    documents: List[str] = [] # Document IDs
    notes: List[str] = [] # Note IDs
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class NotebookResponse(NotebookInDB):
    pass
