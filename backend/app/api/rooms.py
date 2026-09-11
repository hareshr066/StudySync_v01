"""Room management API routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.rooms import CreateRoomRequest, RoomResponse, RoomDetailResponse, RoomListResponse
from app.services.room_service import RoomService
from app.services.deck_service import DeckService
from app.core.dependencies import get_current_user
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/v1/rooms", tags=["Rooms"])


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(request: CreateRoomRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    deck_svc = DeckService()
    if not deck_svc.is_member(request.deck_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    svc = RoomService()
    return svc.create_room(deck_id=request.deck_id, name=request.name, created_by=current_user["_id"])


@router.get("", response_model=RoomListResponse)
async def list_rooms(
    deck_id: Optional[str] = None,
    status_filter: str = "active",
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    svc = RoomService()
    rooms, total = svc.list_rooms(deck_id=deck_id, status=status_filter)
    return {"rooms": rooms, "total": total}


@router.get("/{room_id}", response_model=RoomDetailResponse)
async def get_room(room_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = RoomService()
    room = svc.get_room(room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    members = svc.get_room_members(room_id)
    return {"room": room, "members": members}


@router.post("/{room_id}/join")
async def join_room(room_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = RoomService()
    if not svc.join_room(room_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found or ended")
    return {"message": "Joined room"}


@router.post("/{room_id}/leave")
async def leave_room(room_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = RoomService()
    svc.leave_room(room_id, current_user["_id"])
    return {"message": "Left room"}


@router.post("/{room_id}/end")
async def end_room(room_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = RoomService()
    if not svc.end_room(room_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only room creator can end the room")
    return {"message": "Room ended"}
