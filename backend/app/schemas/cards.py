"""Pydantic schemas for cards."""

from pydantic import BaseModel, Field
from typing import Optional, List


class CreateCardRequest(BaseModel):
    front: str = Field(..., min_length=1, max_length=2000, description="Card front (question)")
    back: str = Field(..., min_length=1, max_length=5000, description="Card back (answer)")
    tags: List[str] = Field(default_factory=list, max_length=20, description="Card tags")
    hint: str = Field("", max_length=500, description="Optional hint")


class UpdateCardRequest(BaseModel):
    front: Optional[str] = Field(None, min_length=1, max_length=2000)
    back: Optional[str] = Field(None, min_length=1, max_length=5000)
    tags: Optional[List[str]] = None
    hint: Optional[str] = Field(None, max_length=500)


class CardResponse(BaseModel):
    id: str
    deck_id: str
    front: str
    back: str
    tags: List[str] = []
    hint: str = ""
    created_by: str
    created_at: str
    updated_at: str


class CardListResponse(BaseModel):
    cards: List[CardResponse]
    total: int
    page: int
    page_size: int


class ImportResultResponse(BaseModel):
    imported: int = 0
    skipped: int = 0
    errors: int = 0
    details: List[str] = []
