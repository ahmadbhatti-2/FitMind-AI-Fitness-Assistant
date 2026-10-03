from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.app.auth import require_path_user
from agent.tools.progress_tool import get_user_progress, update_progress_metric

router = APIRouter()

# Schema for updating metrics
class ProgressUpdate(BaseModel):
    metric_type: str # e.g., 'body_weight'
    value: float

@router.get("/{user_id}", dependencies=[Depends(require_path_user)])
async def read_progress(user_id: str):
    """
    Retrieves the overall fitness progress and metrics of a user.
    """
    try:
        progress = get_user_progress(user_id)
        if "error" in progress:
            raise HTTPException(status_code=404, detail=progress["error"])
        return progress
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update/{user_id}", dependencies=[Depends(require_path_user)])
async def update_progress(user_id: str, data: ProgressUpdate):
    """
    Updates a specific progress metric for the user.
    """
    try:
        result = update_progress_metric(user_id, data.metric_type, data.value)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
