"""Study session API routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.sessions import StartSessionRequest, EndSessionRequest, SessionResponse, SessionListResponse
from app.services.session_service import SessionService
from app.services.deck_service import DeckService
from app.core.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/study/sessions", tags=["Study Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(request: StartSessionRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    deck_svc = DeckService()
    if not deck_svc.is_member(request.deck_id, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    svc = SessionService()
    return svc.start_session(current_user["_id"], request.deck_id)


@router.patch("/{session_id}", response_model=SessionResponse)
async def end_session(session_id: str, request: EndSessionRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = SessionService()
    result = svc.end_session(session_id, current_user["_id"], request.cards_reviewed)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return result


@router.get("", response_model=SessionListResponse)
async def list_sessions(current_user: Dict[str, Any] = Depends(get_current_user)):
    svc = SessionService()
    sessions, total = svc.list_sessions(current_user["_id"])
    return {"sessions": sessions, "total": total}
