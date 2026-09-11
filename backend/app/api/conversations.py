"""AI Conversations API - persistent chat history."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timezone
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.schemas.conversations import ConversationCreate, ConversationResponse, ConversationInDB, AddMessageRequest
from app.schemas.ai import AICitation
from app.db.mongodb import get_database
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])

@router.post("", response_model=ConversationResponse)
def create_conversation(conv: ConversationCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "_id": str(ObjectId()),
        "owner_id": current_user["_id"],
        "notebook_id": conv.notebook_id,
        "title": conv.title,
        "context_type": conv.context_type,
        "context_id": conv.context_id,
        "messages": [],
        "created_at": now,
        "updated_at": now
    }
    db.ai_conversations.insert_one(doc)
    return ConversationInDB(**doc)

@router.get("", response_model=dict)
def list_conversations(
    notebook_id: str = None,
    skip: int = 0, limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    db = get_database()
    query = {"owner_id": current_user["_id"]}
    if notebook_id:
        query["notebook_id"] = notebook_id
    convs = list(db.ai_conversations.find(query).sort("updated_at", -1).skip(skip).limit(limit))
    return {"conversations": [ConversationInDB(**c) for c in convs], "total": len(convs)}

@router.get("/{conv_id}", response_model=ConversationResponse)
def get_conversation(conv_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    conv = db.ai_conversations.find_one({"_id": conv_id, "owner_id": current_user["_id"]})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationInDB(**conv)

@router.patch("/{conv_id}")
def update_conversation_title(conv_id: str, body: dict, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    new_title = body.get("title", "").strip()
    if not new_title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    res = db.ai_conversations.update_one(
        {"_id": conv_id, "owner_id": current_user["_id"]},
        {"$set": {"title": new_title, "updated_at": datetime.now(timezone.utc)}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "updated"}

@router.delete("/{conv_id}")
def delete_conversation(conv_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    res = db.ai_conversations.delete_one({"_id": conv_id, "owner_id": current_user["_id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}

@router.post("/{conv_id}/messages")
async def add_message(
    conv_id: str,
    request: AddMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    db = get_database()
    conv = db.ai_conversations.find_one({"_id": conv_id, "owner_id": current_user["_id"]})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    now = datetime.now(timezone.utc)
    user_msg = {
        "role": "user",
        "content": request.prompt,
        "citations": [],
        "created_at": now
    }

    # Verify context ownership (IDOR prevention)
    context_type = request.context_type or conv.get("context_type")
    context_id = request.context_id or conv.get("context_id")
    
    if context_type and context_id:
        o_refs = [current_user["_id"]]
        if len(str(current_user["_id"])) == 24:
            try:
                o_refs.append(ObjectId(str(current_user["_id"])))
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

    try:
        if not ai_service.is_available():
            raise HTTPException(status_code=503, detail="AI service is not configured. Please set GEMINI_API_KEY.")
        
        result = await ai_service.generate_response(
            prompt=request.prompt,
            context_type=context_type,
            context_id=context_id,
            owner_id=current_user["_id"],
            mode=request.mode or "explain"
        )
        
        ai_msg = {
            "role": "assistant",
            "content": result["text"],
            "citations": result.get("citations", []),
            "created_at": datetime.now(timezone.utc)
        }
        
        db.ai_conversations.update_one(
            {"_id": conv_id},
            {
                "$push": {"messages": {"$each": [user_msg, ai_msg]}},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        
        return {"user_message": user_msg, "ai_message": ai_msg}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)[:200]}")
