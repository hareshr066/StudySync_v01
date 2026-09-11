"""Pydantic schemas for study groups."""

from pydantic import BaseModel, Field
from typing import Optional, List


class CreateGroupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Group name")
    description: str = Field("", max_length=1000, description="Group description")


class UpdateGroupRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class GroupResponse(BaseModel):
    id: str
    name: str
    description: str
    owner_id: str
    owner_name: Optional[str] = None
    member_count: int = 0
    invite_token: Optional[str] = None
    created_at: str
    updated_at: str


class GroupMemberResponse(BaseModel):
    user_id: str
    name: str
    role: str
    joined_at: str


class GroupDetailResponse(BaseModel):
    group: GroupResponse
    members: List[GroupMemberResponse]


class GroupListResponse(BaseModel):
    groups: List[GroupResponse]
    total: int


class GroupInviteResponse(BaseModel):
    invite_token: str
    invite_url: str
