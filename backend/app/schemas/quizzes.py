from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: str = "medium"

class QuizInDB(BaseModel):
    id: str = Field(alias="_id")
    owner_id: str
    notebook_id: Optional[str] = None
    context_type: Optional[str] = None
    context_id: Optional[str] = None
    title: str
    questions: List[QuizQuestion]
    created_at: datetime

    class Config:
        populate_by_name = True

class QuizResponse(QuizInDB):
    pass

class QuizAttempt(BaseModel):
    answers: List[str]  # user's answers indexed by question

class QuizResult(BaseModel):
    score: int
    total: int
    percentage: float
    results: List[dict]  # per-question: {question, user_answer, correct_answer, is_correct, explanation}
