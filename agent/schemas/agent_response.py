from pydantic import BaseModel
from typing import Optional, Union
from agent.schemas.workout_schema import WorkoutRecommendation
from agent.schemas.meal_schema import MealRecommendation

class AgentResponse(BaseModel):
    message: str # Natural language response from Agent
    recommendation_type: Optional[str] = None # 'workout', 'meal', or 'none'
    data: Optional[Union[WorkoutRecommendation, MealRecommendation, dict]] = None
