from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
from backend.app.auth import require_path_user
from agent.tools.user_tool import get_user_profile, update_user_profile

router = APIRouter()

# Schemas for Request/Response
class ProfileUpdate(BaseModel):
    age: Optional[int] = Field(default=None, ge=13, le=120)
    gender: Optional[Literal["female", "male", "other"]] = None
    height: Optional[float] = Field(default=None, ge=80, le=250)
    weight: Optional[float] = Field(default=None, ge=25, le=350)
    goal: Optional[Literal["general_fitness", "muscle_gain", "fat_loss", "strength"]] = None
    experience: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    training_days: Optional[int] = Field(default=None, ge=1, le=7)
    equipment: Optional[list[str]] = None
    diet_preference: Optional[Literal["omnivore", "vegetarian", "vegan", "pescatarian"]] = None
    allergies: Optional[list[str]] = None
    restrictions: Optional[list[str]] = None
    injuries: Optional[list[str]] = None

@router.get("/profile/{user_id}", dependencies=[Depends(require_path_user)])
async def read_profile(user_id: str):
    """
    Retrieves the fitness profile of a user.
    """
    profile = get_user_profile(user_id)
    if "error" in profile:
        raise HTTPException(status_code=404, detail=profile["error"])
    return profile

@router.put("/profile/{user_id}", dependencies=[Depends(require_path_user)])
async def edit_profile(user_id: str, data: ProfileUpdate):
    """
    Updates the fitness profile of a user.
    """
    # Convert Pydantic model to dict, removing None values
    update_data = data.model_dump(exclude_unset=True)
    result = update_user_profile(user_id, update_data)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
