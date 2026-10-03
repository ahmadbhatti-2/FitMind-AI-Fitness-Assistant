from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.app.auth import require_path_user
from typing import Literal, Optional
from agent.tools.feedback_tool import save_feedback, get_user_feedback_summary

router = APIRouter()

# Schema for saving feedback
class FeedbackRequest(BaseModel):
    item_id: str
    item_type: Literal["workout", "meal"]
    feedback_type: Literal["liked", "disliked", "too_hard", "too_easy"]
    comments: Optional[str] = ""

@router.post("/save/{user_id}", dependencies=[Depends(require_path_user)])
async def post_feedback(
    user_id: str, data: FeedbackRequest
):
    """
    Saves user feedback for a specific exercise or meal.
    """
    try:
        result = save_feedback(
            user_id=user_id, 
            item_id=data.item_id, 
            item_type=data.item_type,
            feedback_type=data.feedback_type, 
            comments=data.comments
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{user_id}", dependencies=[Depends(require_path_user)])
async def read_feedback_summary(user_id: str):
    """
    Retrieves a summary of the user's dislikes.
    """
    try:
        summary = get_user_feedback_summary(user_id)
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
