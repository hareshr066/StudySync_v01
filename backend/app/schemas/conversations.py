from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    citations: List[Any] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now())

class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    context_type: Optional[str] = None
    context_id: Optional[str] = None
    notebook_id: Optional[str] = None

class ConversationInDB(BaseModel):
    id: str = Field(alias="_id")
    owner_id: str
    notebook_id: Optional[str] = None
    title: str
    context_type: Optional[str] = None
    context_id: Optional[str] = None
    messages: List[ConversationMessage] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class ConversationResponse(ConversationInDB):
    pass

class AddMessageRequest(BaseModel):
    prompt: str
    mode: str = "explain"
    context_type: Optional[str] = None
    context_id: Optional[str] = None
