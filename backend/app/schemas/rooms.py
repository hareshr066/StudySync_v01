"""Pydantic schemas for study rooms."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class RoomStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"


class CreateRoomRequest(BaseModel):
    deck_id: str = Field(..., description="Deck ID for this study room")
    name: str = Field(..., min_length=1, max_length=200, description="Room name")


class RoomResponse(BaseModel):
    id: str
    deck_id: str
    deck_title: Optional[str] = None
    created_by: str
    creator_name: Optional[str] = None
    name: str
    status: str
    member_count: int = 0
    created_at: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None


class RoomMemberResponse(BaseModel):
    user_id: str
    name: str
    status: str
    joined_at: str
    is_online: bool = False


class RoomDetailResponse(BaseModel):
    room: RoomResponse
    members: List[RoomMemberResponse]


class RoomListResponse(BaseModel):
    rooms: List[RoomResponse]
    total: int
