"""Study Plans API."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.schemas.study_plans import StudyPlanInDB, StudyPlanResponse
from app.schemas.ai import AIStudyPlanSpec
from app.db.mongodb import get_database
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/study-plans", tags=["study_plans"])

@router.post("/generate", response_model=StudyPlanResponse)
async def generate_study_plan(
    request: AIStudyPlanSpec,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    try:
        plan_data = await ai_service.generate_study_plan(
            goal=request.goal,
            exam_date=request.exam_date,
            minutes_per_day=request.minutes_per_day,
            deck_ids=request.deck_ids,
            owner_id=current_user["_id"]
        )
        
        now = datetime.now(timezone.utc)
        plan_doc = {
            "_id": str(ObjectId()),
            "owner_id": current_user["_id"],
            "goal": plan_data["goal"],
            "exam_date": plan_data["exam_date"],
            "minutes_per_day": request.minutes_per_day,
            "days": plan_data["days"],
            "created_at": now
        }
        db = get_database()
        db.study_plans.insert_one(plan_doc)
        return StudyPlanInDB(**plan_doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Study plan error: {e}")
        raise HTTPException(status_code=500, detail=str(e)[:200])

@router.get("", response_model=dict)
def list_study_plans(current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    plans = list(db.study_plans.find({"owner_id": current_user["_id"]}).sort("created_at", -1).limit(20))
    return {"plans": [StudyPlanInDB(**p) for p in plans], "total": len(plans)}

@router.get("/{plan_id}", response_model=StudyPlanResponse)
def get_study_plan(plan_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    plan = db.study_plans.find_one({"_id": plan_id, "owner_id": current_user["_id"]})
    if not plan:
        raise HTTPException(status_code=404, detail="Study plan not found")
    return StudyPlanInDB(**plan)

@router.delete("/{plan_id}")
def delete_study_plan(plan_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    res = db.study_plans.delete_one({"_id": plan_id, "owner_id": current_user["_id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"status": "deleted"}
