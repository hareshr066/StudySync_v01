"""Card management API routes."""

from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File
from app.schemas.cards import CreateCardRequest, UpdateCardRequest, CardResponse, CardListResponse, ImportResultResponse
from app.services.card_service import CardService
from app.services.deck_service import DeckService
from app.core.dependencies import get_current_user
from fastapi.responses import PlainTextResponse
from typing import Dict, Any

router = APIRouter(prefix="/api/v1", tags=["Cards"])


@router.get("/decks/{deck_id}/cards", response_model=CardListResponse)
async def list_cards(
    deck_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    deck_svc = DeckService()
    if not deck_svc.is_member(deck_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    card_svc = CardService()
    cards, total = card_svc.list_cards(deck_id, page, page_size)
    return {"cards": cards, "total": total, "page": page, "page_size": page_size}


@router.post("/decks/{deck_id}/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(deck_id: str, request: CreateCardRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    deck_svc = DeckService()
    if not deck_svc.is_owner(deck_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only deck owner can add cards")
    card_svc = CardService()
    return card_svc.create_card(
        deck_id=deck_id,
        front=request.front,
        back=request.back,
        created_by=current_user["_id"],
        tags=request.tags,
        hint=request.hint
    )


@router.post("/decks/{deck_id}/cards/import", response_model=ImportResultResponse)
async def import_cards_csv(
    deck_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Must be a CSV file")
        
    deck_svc = DeckService()
    if not deck_svc.is_owner(deck_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only deck owner can import cards")
        
    content = await file.read()
    try:
        csv_text = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a UTF-8 encoded CSV.")
        
    card_svc = CardService()
    result = card_svc.import_csv(deck_id, csv_text, current_user["_id"])
    return result


@router.get("/decks/{deck_id}/cards/export", response_class=PlainTextResponse)
async def export_cards_csv(deck_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    deck_svc = DeckService()
    if not deck_svc.is_owner(deck_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only deck owner can export cards")
        
    card_svc = CardService()
    csv_text = card_svc.export_csv(deck_id)
    return PlainTextResponse(content=csv_text, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="deck_{deck_id}.csv"'})


@router.patch("/cards/{card_id}", response_model=CardResponse)
async def update_card(card_id: str, request: UpdateCardRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    card_svc = CardService()
    card = card_svc.get_card(card_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    deck_svc = DeckService()
    if not deck_svc.is_owner(card["deck_id"], current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only deck owner can edit cards")
    updates = request.model_dump(exclude_unset=True)
    result = card_svc.update_card(card_id, updates)
    return result


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(card_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    card_svc = CardService()
    card = card_svc.get_card(card_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    deck_svc = DeckService()
    if not deck_svc.is_owner(card["deck_id"], current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only deck owner can delete cards")
    card_svc.delete_card(card_id)
