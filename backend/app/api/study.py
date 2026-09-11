"""Study API routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.study import SubmitReviewRequest, StudyCardResponse, ReviewResultResponse, StudyStatsResponse
from app.services.study_service import StudyService
from app.services.deck_service import DeckService
from app.core.dependencies import get_current_user
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/v1/study", tags=["Study"])


@router.get("/{deck_id}/next", response_model=Optional[StudyCardResponse])
async def get_next_card(deck_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    deck_svc = DeckService()
    if not deck_svc.is_member(deck_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    svc = StudyService()
    card = svc.get_next_card(deck_id, current_user["_id"])
    if card is None:
        return None
    return card


@router.post("/review", response_model=ReviewResultResponse)
async def submit_review(request: SubmitReviewRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    deck_svc = DeckService()
    if not deck_svc.is_member(request.deck_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    svc = StudyService()
    return svc.submit_review(user_id=current_user["_id"], card_id=request.card_id, rating=request.rating.value)


@router.get("/{deck_id}/stats", response_model=StudyStatsResponse)
async def get_deck_stats(deck_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    deck_svc = DeckService()
    if not deck_svc.is_member(deck_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    svc = StudyService()
    return svc.get_deck_stats(deck_id, current_user["_id"])


@router.get("/stats/overall", response_model=StudyStatsResponse)
async def get_overall_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = StudyService()
    return svc.get_overall_stats(current_user["_id"])
