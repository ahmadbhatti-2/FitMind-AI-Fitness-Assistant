# FitMind

AI-powered personalized fitness recommendations and coaching.

FitMind is a full-stack fitness application that brings workout planning, nutrition recommendations, progress tracking, and an AI fitness coach into one experience. Recommendations use a member's profile, preferences, equipment, recorded injuries, and recent activity alongside a curated fitness catalog.

## Technology

- React 19 and Vite for the web application
- Python 3.11+ and FastAPI for the API
- PostgreSQL and SQLAlchemy for application data
- LangGraph and LangChain for the AI coach workflow
- Google Gemini for conversational coaching
- JSON catalogs for workout, exercise, food, and meal data

## Architecture

```text
Member
  |
  v
React web application
  |
  v
FastAPI
  |-- Authentication and profile routes
  |-- Workout and nutrition recommendation routes
  |-- Progress and feedback routes
  |
  `-- AI coach route
        |
        v
      LangGraph workflow
        |-- Loads the member profile, workout history, and feedback
        |-- Calls workout, meal, progress, and history tools as needed
        |-- Applies recovery and safety checks
        `-- Gemini generates the conversational response
              |
              v
        PostgreSQL and fitness JSON catalogs
```

The workout and meal recommendation endpoints use the project's catalog and recommendation rules. The AI coach uses LangGraph and Gemini, with tools that retrieve member-specific context and fitness recommendations.

## Features

- Account registration and sign-in with hashed passwords and expiring API tokens
- Profile-aware workout recommendations using goals, experience, equipment, recent activity, and recorded injuries
- Meal recommendations that consider dietary preferences, goals, logged meals, and recorded allergens
- Workout and meal history, feedback, progress measurements, and consistency summaries
- AI coach conversations grounded in the signed-in member's profile and recent workout history
- Responsive dashboard and navigation for desktop and mobile

## Requirements

- Python 3.11 or newer
- Node.js 20.19 or newer, or 22.12 or newer
- PostgreSQL
- Google AI Studio API key for AI coach conversations

## Local setup

Run these commands in Windows PowerShell from the `FitMind` repository root: the folder containing `backend\`, `frontend\`, and `requirements-dev.txt`. If your terminal is currently in the parent `AI Fitness Recommendation Agent` folder, first run:

```powershell
Set-Location .\FitMind
```

Create `.venv` from the `FitMind` folder so the Python commands below can find it. Do not run `py -m venv .venv` from the parent folder.

### Install dependencies

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm --prefix .\frontend install
Copy-Item .env.example .env
```

Edit `.env` and set `DATABASE_URL` to your local PostgreSQL connection. For example:

```dotenv
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/fitmind_db
GOOGLE_API_KEY=your-google-ai-studio-key
```

Create the `fitmind_db` database before starting the API. With PostgreSQL command-line tools installed, one option is:

```powershell
createdb -U postgres fitmind_db
```

Initialize a new database with the project schema:

```powershell
psql "$env:DATABASE_URL" -f .\database\schema.sql
```

Run the schema command only when creating a new, empty database. Do not run it again against a database that already has the schema. Keep `.env` private and never commit real credentials.

The `GOOGLE_API_KEY` is needed for AI coach responses. Set it in `.env` before using that feature.

## Run the application

Start the API and web application in separate PowerShell terminals, both from the `FitMind` repository root (the folder containing `backend\` and `frontend\`). If a terminal starts in the parent folder, run `Set-Location .\FitMind` before starting either service.

API:

```powershell
..\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Web application:

```powershell
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`. The API health endpoint is `http://127.0.0.1:8000/`, and interactive API documentation is available at `http://127.0.0.1:8000/docs`.

The frontend uses `http://127.0.0.1:8000` by default. To use another API URL, set `VITE_API_BASE_URL` before starting Vite:

```powershell
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev
```

## Checks

Run the frontend production build and linter from the repository root:

```powershell
npm run build
npm run lint
```

Run the Python test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests
```

## Project structure

```text
backend/       FastAPI routes, authentication, and database models
agent/         LangGraph workflow and member-context tools
recommendation/Workout and meal recommendation rules
database/      PostgreSQL schema
data/          Static exercise, food, workout, and meal catalogs
frontend/      React application
tests/         Python tests
```

## Scope

FitMind is an educational fitness project, not a medical product. Its recommendations do not replace advice from qualified health professionals.
