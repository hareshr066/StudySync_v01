"""Pydantic schemas for notifications."""

from pydantic import BaseModel, Field
from typing import Optional, List


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    read: bool = False
    created_at: str


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
