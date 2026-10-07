from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class ExerciseDetail(BaseModel):
    id: str
    name: str
    sets: Optional[int] = 3
    reps: Optional[str] = "10-12"
    rest: Optional[str] = "60 sec"
    intensity: Optional[str] = None
    weight_kg: Optional[float] = None
    progression: Optional[str] = None

class WorkoutRecommendation(BaseModel):
    title: str
    duration_minutes: int
    difficulty: str
    muscle_groups: List[str]
    exercises: List[ExerciseDetail]
    reasons: List[str]
    safety_note: Optional[str] = None
    weekly_schedule: Optional[List[Dict[str, Any]]] = None
