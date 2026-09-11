"""User API routes for profile/settings."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.users import UpdateProfileRequest, ProfileResponse
from app.core.dependencies import get_current_user
from app.db.mongodb import get_database
from bson import ObjectId
from datetime import datetime
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me/profile", response_model=ProfileResponse)
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    user = db.users.find_one({"_id": ObjectId(current_user["_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "avatar_url": user.get("avatar_url"),
        "daily_goal": user.get("daily_goal", 30),
        "theme": user.get("theme", "light"),
        "current_streak": user.get("current_streak", 0),
        "longest_streak": user.get("longest_streak", 0),
        "created_at": user["created_at"].isoformat() if isinstance(user.get("created_at"), datetime) else str(user.get("created_at", ""))
    }


@router.patch("/me/profile", response_model=ProfileResponse)
async def update_profile(request: UpdateProfileRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    updates = request.model_dump(exclude_unset=True)
    if not updates:
        return await get_profile(current_user)
        
    db.users.update_one({"_id": ObjectId(current_user["_id"])}, {"$set": updates})
    return await get_profile(current_user)
