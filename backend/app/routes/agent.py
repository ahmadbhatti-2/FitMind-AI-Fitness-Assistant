from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.app.auth import get_current_user
from backend.app.database.models import User
from agent.agent import run_fitness_agent

# Create router for Agent endpoints
router = APIRouter()

# Request schema for the chat endpoint
class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_agent(request: ChatRequest, user: User = Depends(get_current_user)):
    """
    Endpoint to send messages to the AI Fitness Agent and get personalized recommendations.
    """
    try:
        # Call the LangGraph agent logic
        response = await run_fitness_agent(
            user_id=str(user.user_id),
            user_input=request.message
        )
        
        if response["status"] == "error":
            raise HTTPException(status_code=500, detail=response["message"])
            
        return response

    except Exception as e:
        # Log the error and return a professional error message
        print(f"Route error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error occurred while processing the request.")
