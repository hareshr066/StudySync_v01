"""Pydantic schemas for study sessions."""

from pydantic import BaseModel, Field
from typing import Optional, List


class StartSessionRequest(BaseModel):
    deck_id: str = Field(..., description="Deck being studied")


class EndSessionRequest(BaseModel):
    cards_reviewed: int = Field(0, ge=0, description="Number of cards reviewed")


class SessionResponse(BaseModel):
    id: str
    deck_id: str
    deck_title: Optional[str] = None
    started_at: str
    ended_at: Optional[str] = None
    cards_reviewed: int = 0
    duration_seconds: int = 0


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int
