# FitMind

FitMind is a full-stack fitness coaching demo. Each account has a fitness profile, a workout and meal log, progress measurements, and personalized recommendations. Recommendation endpoints use the workout and meal catalog with the signed-in user's profile and history. The AI Coach uses Gemini and receives the signed-in user's profile and recent workout context.

## Requirements

- Python 3.11 or newer
- Node.js 20.19+ or 22.12+
- PostgreSQL
- A Google AI Studio API key to use AI Coach

## First-time setup (Windows PowerShell)

From the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\FitMind\requirements-dev.txt
npm --prefix .\frontend install
Copy-Item .\FitMind\.env.example .\FitMind\.env
```

Edit `FitMind/.env` with your PostgreSQL connection string and Google AI key. Create a PostgreSQL database named `fitmind` first. To initialize an empty database, run:

```powershell
psql $env:DATABASE_URL -f .\FitMind\database\schema.sql
```

The schema command is for a new database; do not rerun it over an existing schema. Keep `.env` private and do not commit real credentials.

## Run locally

Open two terminals at the project root.

Terminal 1 — API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --app-dir FitMind --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — frontend:

```powershell
npm run dev
```

Open the Vite URL printed by the frontend terminal (normally `http://localhost:5173`). Sign up for an account and finish setting your profile. The API health check is `http://127.0.0.1:8000/`; interactive API documentation is at `http://127.0.0.1:8000/docs`.

To use a different API URL, set `VITE_API_BASE_URL` before starting Vite, for example `$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"`.

## Quality checks

```powershell
npm run build
npm run lint
```

Python recommendation tests are in `FitMind/tests/`. From the project root, run:

```powershell
Set-Location .\FitMind
..\.venv\Scripts\python.exe -m pytest .\tests
```

## Main features

- Account registration and sign-in with hashed passwords and expiring API tokens.
- Profile-aware workout choices that consider experience, equipment, recent workouts, and recorded injuries.
- Meal suggestions filtered by dietary preference, goal, logged meals, and recorded allergens.
- Workout completion/rest-day logging, meal logging, feedback, weight history, and progress summaries.
- Gemini-powered coach chat that loads the active user's profile and workout history for each request.
- Responsive dashboard and navigation for desktop and mobile.

FitMind is an educational project, not a medical product. Its recommendations do not replace advice from qualified health professionals.
