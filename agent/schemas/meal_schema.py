from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class MealPortion(BaseModel):
    food_id: str
    food_name: str
    amount_g: int
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

class MealRecommendation(BaseModel):
    id: str
    meal_name: str
    meal_type: str # e.g., breakfast, lunch
    ingredients: List[str]
    portions: List[MealPortion]
    is_high_protein: bool
    reasons: List[str]
    alternatives: List[str]
    calories_est: Optional[int] = None
    macros: Optional[Dict[str, float]] = None
    daily_targets: Optional[Dict[str, Any]] = None
    meal_target: Optional[Dict[str, Optional[float]]] = None
