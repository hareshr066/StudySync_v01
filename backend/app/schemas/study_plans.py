from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DayPlan(BaseModel):
    day: int
    date: str
    topic: str
    activity: str
    duration_minutes: int
    tips: str = ""

class StudyPlanInDB(BaseModel):
    id: str = Field(alias="_id")
    owner_id: str
    goal: str
    exam_date: str
    minutes_per_day: int
    days: List[DayPlan]
    created_at: datetime

    class Config:
        populate_by_name = True

class StudyPlanResponse(StudyPlanInDB):
    pass
