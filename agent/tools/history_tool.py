import logging
from datetime import date
from sqlalchemy.orm import Session
from backend.app.database.connection import SessionLocal
from backend.app.database.models import MealHistory, User, WorkoutHistory

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_workout_history(
    user_id: str,
    template_id: str,
    muscle_group: str,
    status: str,
    difficulty_felt: str = None,
    workout_date: date = None,
    performance: dict | None = None,
):
    """Persists a completed or skipped workout for a real user."""
    db: Session = SessionLocal()
    try:
        uid = int(user_id)
        if not db.query(User.user_id).filter(User.user_id == uid).first():
            return {"error": "User not found."}

        entry = WorkoutHistory(
            user_id=uid,
            template_id=template_id,
            muscle_group=muscle_group,
            status=status,
            difficulty_felt=difficulty_felt,
            performance=performance,
        )
        if workout_date is not None:
            entry.workout_date = workout_date

        db.add(entry)
        db.commit()
        db.refresh(entry)
        return {"status": "success", "history_id": entry.history_id}
    except ValueError:
        return {"error": "Invalid User ID format."}
    except Exception as e:
        db.rollback()
        logger.error(f"DB error saving workout history: {e}")
        return {"error": "Failed to save workout history."}
    finally:
        db.close()

def log_meal_history(
    user_id: str,
    meal_id: str,
    meal_type: str,
    meal_date: date = None,
):
    """Persists a meal log for a real user."""
    db: Session = SessionLocal()
    try:
        uid = int(user_id)
        if not db.query(User.user_id).filter(User.user_id == uid).first():
            return {"error": "User not found."}

        entry = MealHistory(
            user_id=uid,
            meal_id=meal_id,
            meal_type=meal_type,
        )
        if meal_date is not None:
            entry.meal_date = meal_date

        db.add(entry)
        db.commit()
        db.refresh(entry)
        return {"status": "success", "meal_log_id": entry.meal_log_id}
    except ValueError:
        return {"error": "Invalid User ID format."}
    except Exception as e:
        db.rollback()
        logger.error(f"DB error saving meal history: {e}")
        return {"error": "Failed to save meal history."}
    finally:
        db.close()

def get_workout_history(user_id: str):
    """
    Retrieves real workout history from PostgreSQL database.
    """
    db: Session = SessionLocal()
    try:
        uid = int(user_id)
        # Fetch all workouts for the user, ordered by date descending
        workouts = db.query(WorkoutHistory).filter(
            WorkoutHistory.user_id == uid
        ).order_by(
            WorkoutHistory.workout_date.desc(),
            WorkoutHistory.created_at.desc(),
        ).all()
        
        # Convert SQLAlchemy objects to a list of dictionaries
        return [
            {
                "template_id": w.template_id,
                "date": str(w.workout_date),
                "muscle_group": w.muscle_group,
                "status": w.status,
                "difficulty": w.difficulty_felt,
                "performance": w.performance or {},
            } for w in workouts
        ]

    except ValueError:
        return {"error": "Invalid User ID format."}
    except Exception as e:
        logger.error(f"DB error retrieving workout history: {e}")
        return {"error": "An internal database error occurred."}
    finally:
        db.close()

def get_meal_history(user_id: str):
    """
    Retrieves real meal history from PostgreSQL database.
    """
    db: Session = SessionLocal()
    try:
        uid = int(user_id)
        meals = db.query(MealHistory).filter(MealHistory.user_id == uid).order_by(MealHistory.meal_date.desc()).all()
        
        return [
            {
                "date": str(m.meal_date),
                "meal_type": m.meal_type,
                "food": m.meal_id # In real DB, meal_id references meal_templates.json
            } for m in meals
        ]

    except ValueError:
        return {"error": "Invalid User ID format."}
    except Exception as e:
        logger.error(f"DB error retrieving meal history: {e}")
        return {"error": "An internal database error occurred."}
    finally:
        db.close()

def get_last_trained_muscle(user_id: str):
    """
    Retrieves the most recent muscle group trained from the database.
    """
    db: Session = SessionLocal()
    try:
        uid = int(user_id)
        # Get the single most recent completed workout
        last_workout = db.query(WorkoutHistory).filter(
            WorkoutHistory.user_id == uid, 
            WorkoutHistory.status == "completed"
        ).order_by(WorkoutHistory.workout_date.desc()).first()
        
        return last_workout.muscle_group if last_workout else None

    except ValueError:
        return None
    except Exception as e:
        logger.error(f"DB error getting last trained muscle: {e}")
        return None
    finally:
        db.close()
