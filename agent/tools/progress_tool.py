import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.app.database.connection import SessionLocal
from backend.app.database.models import Profile, Progress, WorkoutHistory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_progress(user_id: str):
    """
    Queries real user fitness progress metrics from PostgreSQL storage.
    """
    db: Session = SessionLocal()
    try:
        # Validate integer user ID format before DB execution
        uid = int(user_id)
        
        # Query weight tracking records ordered chronologically
        weight_data = db.query(Progress).filter(
            Progress.user_id == uid, 
            Progress.metric_type == 'body_weight'
        ).order_by(Progress.metric_date.asc()).all()
        
        weight_history = [{"date": str(p.metric_date), "weight": p.weight} for p in weight_data]

        # Aggregate total completed workout sessions count
        completed_workouts = db.query(WorkoutHistory.workout_date).filter(
            WorkoutHistory.user_id == uid, 
            WorkoutHistory.status == "completed"
        ).all()
        total_completed = len(completed_workouts)

        profile = db.query(Profile).filter(Profile.user_id == uid).first()
        training_days = profile.training_days if profile else None
        today = date.today()
        recent_start = today - timedelta(days=29)
        recent_completed = sum(
            1 for (workout_date,) in completed_workouts
            if workout_date and recent_start <= workout_date <= today
        )

        expected_sessions = training_days * 30 / 7 if training_days else 0
        consistency_percentage = (
            min(round(recent_completed / expected_sessions * 100), 100)
            if expected_sessions > 0
            else 0
        )

        weekly_counts = {}
        if training_days and training_days > 0:
            for (workout_date,) in completed_workouts:
                if workout_date and workout_date <= today:
                    week_start = workout_date - timedelta(days=workout_date.weekday())
                    weekly_counts[week_start] = weekly_counts.get(week_start, 0) + 1

        current_week = today - timedelta(days=today.weekday())
        if training_days and weekly_counts.get(current_week, 0) < training_days:
            current_week -= timedelta(days=7)

        current_streak = 0
        while training_days and weekly_counts.get(current_week, 0) >= training_days:
            current_streak += 1
            current_week -= timedelta(days=7)

        return {
            "weight_history": weight_history,
            "total_workouts_completed": total_completed,
            "consistency_percentage": consistency_percentage,
            "current_streak": current_streak,
            "last_milestone": "Weight data updated" if weight_history else "No data yet"
        }

    except ValueError:
        return {"error": "Invalid User ID format."}
    except Exception as e:
        logger.error(f"DB error retrieving progress: {e}")
        return {"error": "An internal database error occurred."}
    finally:
        # Always release DB session connection back to pool
        db.close()

def update_progress_metric(user_id: str, metric_type: str, value: float):
    """
    Persists a new user progress metric record into PostgreSQL storage.
    """
    db: Session = SessionLocal()
    try:
        uid = int(user_id)
        
        # Build and stage new ORM metric entry
        new_entry = Progress(
            user_id=uid,
            metric_type=metric_type,
            weight=value
        )
        
        db.add(new_entry)
        db.commit()
        
        logger.info(f"Progress metric {metric_type} updated for user {uid}")
        return {"status": "success", "message": f"{metric_type} updated successfully in database."}

    except ValueError:
        return {"error": "Invalid User ID format."}
    except Exception as e:
        # Revert staged operations on persistence failures to maintain consistency
        db.rollback()
        logger.error(f"DB error updating progress: {e}")
        return {"error": "Failed to update progress in database."}
    finally:
        db.close()