from datetime import date
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.app.auth import require_path_user
from agent.tools.history_tool import get_workout_history, log_workout_history
from agent.tools.workout_tool import recommend_workout

router = APIRouter()

class WorkoutHistoryCreate(BaseModel):
    template_id: str
    muscle_group: str
    status: Literal["completed", "skipped"] = "completed"
    difficulty_felt: Optional[str] = None
    workout_date: Optional[date] = None
    performance: Optional[dict[str, dict[str, float | int | str]]] = None

@router.get("/history/{user_id}", dependencies=[Depends(require_path_user)])
async def read_workout_history(user_id: str):
    """
    Retrieves all previous workouts for a specific user.
    """
    try:
        history = get_workout_history(user_id)
        if isinstance(history, dict) and "error" in history:
            raise HTTPException(status_code=404, detail=history["error"])
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/history/{user_id}", dependencies=[Depends(require_path_user)])
async def create_workout_history(
    user_id: str,
    data: WorkoutHistoryCreate,
):
    result = log_workout_history(user_id, **data.model_dump(exclude_none=True))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/recommend/{user_id}", dependencies=[Depends(require_path_user)])
async def get_direct_recommendation(user_id: str):
    """
    Provides a direct workout recommendation without a chat interface.
    Useful for the Dashboard 'Today's Workout' card.
    """
    try:
        recommendation = recommend_workout(user_id)
        if "error" in recommendation:
            raise HTTPException(status_code=400, detail=recommendation["error"])
        return recommendation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
