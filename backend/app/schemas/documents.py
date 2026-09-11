from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DocumentBase(BaseModel):
    title: str = Field(..., description="Document title")
    description: Optional[str] = None
    tags: List[str] = []

class DocumentCreate(DocumentBase):
    pass

class DocumentInDB(DocumentBase):
    id: str = Field(alias="_id")
    owner_id: str
    filename: str
    mime_type: str
    size: int
    status: str = "uploading"
    gemini_file_id: Optional[str] = None
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True

class DocumentResponse(DocumentInDB):
    pass
