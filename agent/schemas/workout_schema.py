from pydantic import BaseModel
from typing import List, Optional

class ExerciseDetail(BaseModel):
    id: str
    name: str
    sets: Optional[int] = 3
    reps: Optional[str] = "10-12"
    rest: Optional[str] = "60 sec"

class WorkoutRecommendation(BaseModel):
    title: str
    duration_minutes: int
    difficulty: str
    muscle_groups: List[str]
    exercises: List[ExerciseDetail]
    reasons: List[str]
    safety_note: Optional[str] = None
