from pydantic import BaseModel
from typing import List, Optional

class MealRecommendation(BaseModel):
    meal_name: str
    meal_type: str # e.g., breakfast, lunch
    ingredients: List[str]
    is_high_protein: bool
    reasons: List[str]
    alternatives: List[str]
    calories_est: Optional[int] = None
