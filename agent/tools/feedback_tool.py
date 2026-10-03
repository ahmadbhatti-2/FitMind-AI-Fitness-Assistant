import logging
from sqlalchemy.orm import Session
from backend.app.database.connection import SessionLocal
from backend.app.database.models import Feedback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_feedback(
    user_id: str,
    item_id: str,
    feedback_type: str,
    comments: str = "",
    item_type: str = "general",
):
    """
    Saves real user feedback for a specific workout or meal in PostgreSQL.
    """
    db: Session = SessionLocal()
    try:
        uid = int(user_id)
        
        # Create a new Feedback record
        new_feedback = Feedback(
            user_id=uid,
            item_id=item_id,
            item_type=item_type,
            feedback_type=feedback_type,
            comments=comments
        )

        db.add(new_feedback)
        db.commit()
        logger.info(f"Feedback saved for user {uid} on item {item_id}")
        return {
            "status": "success", 
            "message": "Thank you for your feedback! I'll use this to improve your future plans."
        }

    except ValueError:
        return {"error": "Invalid User ID format."}
    except Exception as e:
        db.rollback()
        logger.error(f"DB error saving feedback: {e}")
        return {"error": "Failed to save feedback in database."}
    finally:
        db.close()

def get_user_feedback_summary(user_id: str):
    """
    Retrieves real dislikes summary from PostgreSQL to avoid repeating disliked items.
    """
    db: Session = SessionLocal()
    try:
        uid = int(user_id)
        
        # Query all 'disliked' feedback for this user
        dislikes = db.query(Feedback).filter(
            Feedback.user_id == uid, 
            Feedback.feedback_type == "disliked"
        ).all()
        
        # Separate into workouts and meals
        summary = {"workouts": [], "meals": []}
        for f in dislikes:
            if f.item_type == "workout":
                summary["workouts"].append(f.item_id)
            elif f.item_type == "meal":
                summary["meals"].append(f.item_id)
                
        return summary

    except ValueError:
        return {"error": "Invalid User ID format."}
    except Exception as e:
        logger.error(f"DB error retrieving feedback: {e}")
        return {"error": "Failed to retrieve feedback summary."}
    finally:
        db.close()
