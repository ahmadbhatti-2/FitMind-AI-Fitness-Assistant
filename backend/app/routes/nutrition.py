from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.app.auth import get_current_user, require_path_user
from agent.tools.history_tool import get_meal_history
from agent.tools.history_tool import log_meal_history
from agent.tools.diet_tool import get_food_replacement, recommend_meal

router = APIRouter()

class MealHistoryCreate(BaseModel):
    meal_id: str
    meal_type: str
    meal_date: Optional[date] = None

@router.get("/history/{user_id}", dependencies=[Depends(require_path_user)])
async def read_meal_history(user_id: str):
    """
    Retrieves all previous meals consumed by the user.
    """
    try:
        history = get_meal_history(user_id)
        if isinstance(history, dict) and "error" in history:
            raise HTTPException(status_code=404, detail=history["error"])
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/history/{user_id}", dependencies=[Depends(require_path_user)])
async def create_meal_history(
    user_id: str,
    data: MealHistoryCreate,
):
    result = log_meal_history(user_id, **data.model_dump(exclude_none=True))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get(
    "/recommend/{user_id}/{meal_type}",
    dependencies=[Depends(require_path_user)],
)
async def get_direct_meal(user_id: str, meal_type: str):
    if meal_type not in {"breakfast", "lunch", "dinner", "snack"}:
        raise HTTPException(status_code=422, detail="Choose breakfast, lunch, dinner, or snack.")
    """
    Directly recommends a meal based on type (e.g., breakfast, post_workout).
    Useful for the Dashboard 'Next Meal' card.
    """
    try:
        recommendation = recommend_meal(user_id, meal_type)
        if "error" in recommendation:
            raise HTTPException(status_code=400, detail=recommendation["error"])
        return recommendation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/replacement/{food_id}", dependencies=[Depends(get_current_user)])
async def get_replacement(food_id: str):
    """
    Provides healthy alternatives for a specific food item.
    """
    try:
        result = get_food_replacement(food_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
