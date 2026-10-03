import sys
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.routes import agent, auth, users, workouts, nutrition, progress, feedback

# Initialize FastAPI app
app = FastAPI(
    title="FitMind AI Fitness API",
    description="AI-Powered Personalized Fitness Recommendation Agent Backend",
    version="1.0.0"
)

# Setup CORS (Allows Frontend to communicate with Backend)
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routes from different modules
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(agent.router, prefix="/agent", tags=["AI Agent"])
app.include_router(workouts.router, prefix="/workouts", tags=["Workouts"])
app.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition"])
app.include_router(progress.router, prefix="/progress", tags=["Progress"])
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])

@app.get("/")
async def root():
    """
    Health check endpoint to verify if the server is running.
    """
    return {"status": "online", "message": "Welcome to FitMind AI Fitness API"}

if __name__ == "__main__":
    # Run the server using uvicorn
    uvicorn.run(
        "backend.app.main:app",
        app_dir=str(PROJECT_ROOT),
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
