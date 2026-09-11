"""Study group API routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.groups import (
    CreateGroupRequest, UpdateGroupRequest, GroupResponse,
    GroupDetailResponse, GroupListResponse, GroupInviteResponse,
)
from app.services.group_service import GroupService
from app.core.dependencies import get_current_user
from app.core.config import settings
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/groups", tags=["Study Groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(request: CreateGroupRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = GroupService()
    return svc.create_group(owner_id=current_user["_id"], name=request.name, description=request.description)


@router.get("", response_model=GroupListResponse)
async def list_groups(current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = GroupService()
    groups, total = svc.list_user_groups(current_user["_id"])
    return {"groups": groups, "total": total}


@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(group_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = GroupService()
    if not svc.is_member(group_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")
    group = svc.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    members = svc.get_members(group_id)
    return {"group": group, "members": members}


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: str, request: UpdateGroupRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = GroupService()
    try:
        updates = request.model_dump(exclude_unset=True)
        result = svc.update_group(group_id, current_user["_id"], updates)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        return result
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = GroupService()
    try:
        if not svc.delete_group(group_id, current_user["_id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{group_id}/invite", response_model=GroupInviteResponse)
async def generate_invite(group_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = GroupService()
    try:
        token = svc.generate_invite_token(group_id, current_user["_id"])
        invite_url = f"{settings.FRONTEND_URL}/groups/join/{token}"
        return {"invite_token": token, "invite_url": invite_url}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/join/{invite_token}", response_model=GroupResponse)
async def join_by_invite(invite_token: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = GroupService()
    try:
        return svc.join_by_invite(invite_token, current_user["_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{group_id}/leave")
async def leave_group(group_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = GroupService()
    try:
        svc.leave_group(group_id, current_user["_id"])
        return {"message": "Left group"}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{group_id}/members")
async def get_members(group_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = GroupService()
    if not svc.is_member(group_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    return {"members": svc.get_members(group_id)}
