"""Notification API routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.notifications import NotificationListResponse
from app.services.notification_service import NotificationService
from app.core.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = NotificationService()
    items, total, unread = svc.list_for_user(current_user["_id"])
    return {"notifications": items, "total": total, "unread_count": unread}


@router.patch("/{notification_id}/read")
async def mark_read(notification_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = NotificationService()
    if not svc.mark_read(notification_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"message": "Marked as read"}


@router.post("/read-all")
async def mark_all_read(current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = NotificationService()
    count = svc.mark_all_read(current_user["_id"])
    return {"message": f"Marked {count} notifications as read"}
