"""Quiz API - generate and store AI quizzes."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.schemas.quizzes import QuizInDB, QuizResponse, QuizAttempt, QuizResult
from app.schemas.ai import AIQuizSpec
from app.db.mongodb import get_database
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/quizzes", tags=["quizzes"])

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: AIQuizSpec,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    db = get_database()
    
    # IDOR check
    o_refs = [current_user["_id"]]
    if len(str(current_user["_id"])) == 24:
        try:
            o_refs.append(ObjectId(str(current_user["_id"])))
        except Exception:
            pass

    if request.context_type == "document" and request.context_id:
        c_refs = [request.context_id]
        if len(str(request.context_id)) == 24:
            try:
                c_refs.append(ObjectId(str(request.context_id)))
            except Exception:
                pass
        doc = db.documents.find_one({"_id": {"$in": c_refs}, "owner_id": {"$in": o_refs}})
        if not doc:
            raise HTTPException(status_code=403, detail="Access denied")
    elif request.context_type == "notebook" and request.context_id:
        c_refs = [request.context_id]
        if len(str(request.context_id)) == 24:
            try:
                c_refs.append(ObjectId(str(request.context_id)))
            except Exception:
                pass
        nb = db.notebooks.find_one({"_id": {"$in": c_refs}, "owner_id": {"$in": o_refs}})
        if not nb:
            raise HTTPException(status_code=403, detail="Access denied")
    
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    try:
        questions = await ai_service.generate_quiz(
            context_type=request.context_type,
            context_id=request.context_id,
            owner_id=current_user["_id"],
            count=min(request.count, 20),
            difficulty=request.difficulty,
            quiz_type=request.type
        )
        
        now = datetime.now(timezone.utc)
        quiz_doc = {
            "_id": str(ObjectId()),
            "owner_id": current_user["_id"],
            "notebook_id": None,
            "context_type": request.context_type,
            "context_id": request.context_id,
            "title": f"Quiz - {datetime.now(timezone.utc).strftime('%b %d, %Y')}",
            "questions": questions,
            "created_at": now
        }
        db.quizzes.insert_one(quiz_doc)
        return QuizInDB(**quiz_doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e)[:200])

@router.get("", response_model=dict)
def list_quizzes(current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    quizzes = list(db.quizzes.find({"owner_id": current_user["_id"]}).sort("created_at", -1).limit(50))
    return {"quizzes": [QuizInDB(**q) for q in quizzes], "total": len(quizzes)}

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    quiz = db.quizzes.find_one({"_id": quiz_id, "owner_id": current_user["_id"]})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return QuizInDB(**quiz)

@router.post("/{quiz_id}/attempt", response_model=QuizResult)
def attempt_quiz(quiz_id: str, attempt: QuizAttempt, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    quiz = db.quizzes.find_one({"_id": quiz_id, "owner_id": current_user["_id"]})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    questions = quiz["questions"]
    if len(attempt.answers) != len(questions):
        raise HTTPException(status_code=400, detail="Answer count does not match question count")
    
    results = []
    score = 0
    for i, (q, user_ans) in enumerate(zip(questions, attempt.answers)):
        is_correct = user_ans.strip().lower() == q["correct_answer"].strip().lower()
        if is_correct:
            score += 1
        results.append({
            "question": q["question"],
            "user_answer": user_ans,
            "correct_answer": q["correct_answer"],
            "is_correct": is_correct,
            "explanation": q.get("explanation", "")
        })
    
    percentage = (score / len(questions)) * 100 if questions else 0
    now = datetime.now(timezone.utc)
    attempt_doc = {
        "_id": str(ObjectId()),
        "quiz_id": quiz_id,
        "user_id": current_user["_id"],
        "score": score,
        "total": len(questions),
        "percentage": round(percentage, 1),
        "results": results,
        "created_at": now
    }
    db.quiz_attempts.insert_one(attempt_doc)

    return QuizResult(score=score, total=len(questions), percentage=round(percentage, 1), results=results)

@router.get("/{quiz_id}/attempts")
def get_quiz_attempts(quiz_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    u_refs = [current_user["_id"]]
    if len(current_user["_id"]) == 24:
        try:
            u_refs.append(ObjectId(current_user["_id"]))
        except Exception:
            pass
    attempts = list(db.quiz_attempts.find({
        "quiz_id": quiz_id,
        "user_id": {"$in": u_refs}
    }).sort("created_at", -1).limit(20))
    for a in attempts:
        a["_id"] = str(a["_id"])
        if isinstance(a.get("created_at"), datetime):
            a["created_at"] = a["created_at"].isoformat()
    return {"attempts": attempts}

@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_database()
    res = db.quizzes.delete_one({"_id": quiz_id, "owner_id": current_user["_id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Quiz not found")
    db.quiz_attempts.delete_many({"quiz_id": quiz_id})
    return {"status": "deleted"}
