"""Pydantic schemas for study/review."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ReviewRating(str, Enum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


class SubmitReviewRequest(BaseModel):
    card_id: str = Field(..., description="Card ID")
    deck_id: str = Field(..., description="Deck ID for authorization")
    rating: ReviewRating = Field(..., description="Review rating")


class StudyCardResponse(BaseModel):
    """A card presented during study, with review metadata."""
    id: str
    deck_id: str
    front: str
    back: str
    is_new: bool = True
    repetitions: int = 0
    interval: float = 0
    ease_factor: float = 2.5
    due_at: Optional[str] = None


class ReviewResultResponse(BaseModel):
    card_id: str
    repetitions: int
    interval: float
    ease_factor: float
    due_at: str


class StudyStatsResponse(BaseModel):
    total_cards: int = 0
    cards_studied: int = 0
    cards_due: int = 0
    cards_due_today: int = 0
    new_cards: int = 0
    reviewed_today: int = 0
    deck_progress: float = 0.0


class DeckStudyStats(BaseModel):
    deck_id: str
    deck_title: str
    total_cards: int = 0
    cards_due: int = 0
    cards_studied: int = 0
    progress: float = 0.0
