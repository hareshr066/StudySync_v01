from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class AICitation(BaseModel):
    source_id: str
    source_name: str
    page_number: Optional[int] = None
    text_snippet: Optional[str] = None

class AIChatMessage(BaseModel):
    role: str = "user" # user or model
    content: str
    citations: Optional[List[AICitation]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AIConversationCreate(BaseModel):
    title: str = "New Conversation"
    context_type: Optional[str] = None # notebook, document, note
    context_id: Optional[str] = None

class AIConversationInDB(BaseModel):
    id: str = Field(alias="_id")
    owner_id: str
    title: str
    context_type: Optional[str] = None
    context_id: Optional[str] = None
    messages: List[AIChatMessage] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class AIGenerateRequest(BaseModel):
    prompt: str
    context_type: Optional[str] = None
    context_id: Optional[str] = None
    mode: Optional[str] = "explain" # explain, socratic, summarize, quiz

class AIGenerateResponse(BaseModel):
    text: str
    citations: List[AICitation] = []

class AIFlashcardSpec(BaseModel):
    count: int = 5
    difficulty: str = "medium"
    context_type: Optional[str] = None
    context_id: Optional[str] = None

class AIQuizSpec(BaseModel):
    count: int = 5
    difficulty: str = "medium"
    type: str = "mcq"
    context_type: Optional[str] = None
    context_id: Optional[str] = None

class AIStudyPlanSpec(BaseModel):
    goal: str
    exam_date: str
    minutes_per_day: int
    deck_ids: List[str]
