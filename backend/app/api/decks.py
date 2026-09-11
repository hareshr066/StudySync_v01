"""Deck management API routes."""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.schemas.decks import CreateDeckRequest, UpdateDeckRequest, DeckResponse, DeckListResponse, ShareTokenResponse
from app.services.deck_service import DeckService
from app.core.dependencies import get_current_user
from app.core.config import settings
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/v1/decks", tags=["Decks"])


@router.get("", response_model=DeckListResponse)
async def list_decks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=200),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    svc = DeckService()
    if search and search.strip():
        decks, total = svc.search_decks(search, current_user["_id"], page, page_size)
    else:
        decks, total = svc.list_user_decks(current_user["_id"], page, page_size)
    return {"decks": decks, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(request: CreateDeckRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = DeckService()
    return svc.create_deck(
        owner_id=current_user["_id"],
        title=request.title,
        description=request.description,
        visibility=request.visibility.value,
        tags=request.tags,
    )


@router.get("/discover", response_model=DeckListResponse)
async def discover_decks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("popular", pattern="^(popular|recent)$"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    svc = DeckService()
    decks, total = svc.discover_public_decks(page, page_size, sort)
    return {"decks": decks, "total": total, "page": page, "page_size": page_size}


@router.post("/discover/{deck_id}/join", response_model=DeckResponse)
async def join_public_deck(deck_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = DeckService()
    result = svc.join_public_deck(deck_id, current_user["_id"])
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found or not public")
    return result


@router.get("/{deck_id}", response_model=DeckResponse)
async def get_deck(deck_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = DeckService()
    if not svc.is_member(deck_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this deck")
    deck = svc.get_deck(deck_id, current_user["_id"])
    if not deck:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    return deck


@router.patch("/{deck_id}", response_model=DeckResponse)
async def update_deck(deck_id: str, request: UpdateDeckRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = DeckService()
    try:
        updates = request.model_dump(exclude_unset=True)
        if "visibility" in updates and updates["visibility"]:
            updates["visibility"] = updates["visibility"].value
        result = svc.update_deck(deck_id, current_user["_id"], updates)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
        return result
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(deck_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = DeckService()
    try:
        if not svc.delete_deck(deck_id, current_user["_id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{deck_id}/share", response_model=ShareTokenResponse)
async def share_deck(deck_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = DeckService()
    try:
        token = svc.generate_share_token(deck_id, current_user["_id"])
        share_url = f"{settings.FRONTEND_URL}/join/{token}"
        return {"share_token": token, "share_url": share_url}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/join/{share_token}", response_model=DeckResponse)
async def join_deck(share_token: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = DeckService()
    try:
        return svc.join_deck_by_token(share_token, current_user["_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
