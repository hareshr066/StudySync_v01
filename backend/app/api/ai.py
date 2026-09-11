"""AI API routes."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.core.dependencies import get_current_user
from app.schemas.ai import AIGenerateRequest, AIGenerateResponse, AIFlashcardSpec
from app.db.mongodb import get_database
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

def _check_context_access(db, context_type: str, context_id: str, owner_id: str):
    """Verify the user owns the context resource (IDOR prevention)."""
    from bson import ObjectId
    o_refs = [owner_id]
    if len(str(owner_id)) == 24:
        try:
            o_refs.append(ObjectId(str(owner_id)))
        except Exception:
            pass
    c_refs = [context_id]
    if len(str(context_id)) == 24:
        try:
            c_refs.append(ObjectId(str(context_id)))
        except Exception:
            pass

    if context_type == "document":
        doc = db.documents.find_one({"_id": {"$in": c_refs}, "owner_id": {"$in": o_refs}})
        if not doc:
            raise HTTPException(status_code=403, detail="You do not have access to this document")
    elif context_type == "notebook":
        nb = db.notebooks.find_one({"_id": {"$in": c_refs}, "owner_id": {"$in": o_refs}})
        if not nb:
            raise HTTPException(status_code=403, detail="You do not have access to this notebook")

@router.post("/generate", response_model=AIGenerateResponse)
async def generate_answer(
    request: AIGenerateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service is not configured. Please set GEMINI_API_KEY.")
    
    db = get_database()
    if request.context_type and request.context_id:
        _check_context_access(db, request.context_type, request.context_id, current_user["_id"])
    
    try:
        res = await ai_service.generate_response(
            prompt=request.prompt,
            context_type=request.context_type,
            context_id=request.context_id,
            owner_id=current_user["_id"],
            mode=request.mode or "explain"
        )
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e)[:200])

@router.post("/flashcards")
async def generate_flashcards(
    request: AIFlashcardSpec,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service is not configured. Please set GEMINI_API_KEY.")
    
    db = get_database()
    if request.context_type and request.context_id:
        _check_context_access(db, request.context_type, request.context_id, current_user["_id"])
    
    try:
        cards = await ai_service.generate_flashcards(
            count=min(request.count, 30),
            difficulty=request.difficulty,
            context_type=request.context_type,
            context_id=request.context_id,
            owner_id=current_user["_id"]
        )
        return {"cards": cards}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Flashcard generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e)[:200])
