"""Pydantic schemas for users."""

from pydantic import BaseModel, Field
from typing import Optional


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    daily_goal: Optional[int] = Field(None, ge=1, le=500)
    theme: Optional[str] = Field(None, pattern="^(light|dark)$")


class ProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    avatar_url: Optional[str] = None
    daily_goal: int = 30
    theme: str = "light"
    current_streak: int = 0
    longest_streak: int = 0
    created_at: str
