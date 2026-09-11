"""Pydantic schemas for decks."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class DeckVisibility(str, Enum):
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


class CreateDeckRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Deck title")
    description: str = Field("", max_length=1000, description="Deck description")
    visibility: DeckVisibility = Field(DeckVisibility.PRIVATE, description="Deck visibility")
    tags: List[str] = Field(default_factory=list, max_length=20, description="Deck tags")


class UpdateDeckRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    visibility: Optional[DeckVisibility] = None
    tags: Optional[List[str]] = None


class DeckResponse(BaseModel):
    id: str
    owner_id: str
    owner_name: Optional[str] = None
    title: str
    description: str
    visibility: str
    member_count: int = 0
    card_count: int = 0
    cards_due: int = 0
    tags: List[str] = []
    share_token: Optional[str] = None
    created_at: str
    updated_at: str


class DeckListResponse(BaseModel):
    decks: List[DeckResponse]
    total: int
    page: int
    page_size: int


class ShareTokenResponse(BaseModel):
    share_token: str
    share_url: str
