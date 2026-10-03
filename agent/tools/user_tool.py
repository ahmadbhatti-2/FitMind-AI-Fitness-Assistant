import logging
from sqlalchemy.orm import Session
from backend.app.database.connection import SessionLocal
from backend.app.database.models import Profile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_profile(user_id: str):
    """
    Retrieves the real user profile from PostgreSQL database.
    """
    db: Session = SessionLocal()
    try:
        # Convert user_id to int because DB uses SERIAL/Integer
        uid = int(user_id)
        
        # Query the Profile table
        profile = db.query(Profile).filter(Profile.user_id == uid).first()
        
        if not profile:
            logger.warning(f"Profile not found in DB for user_id: {uid}")
            return {"error": "User profile not found in the database."}
            
        # Convert SQLAlchemy model to a dictionary for the Agent
        return {
            "age": profile.age,
            "gender": profile.gender,
            "height": profile.height,
            "weight": profile.weight,
            "goal": profile.goal,
            "experience": profile.experience,
            "training_days": profile.training_days,
            "equipment": profile.equipment, # JSONB field
            "diet_preference": profile.diet_preference,
            "allergies": profile.allergies, # JSONB field
            "restrictions": profile.restrictions, # JSONB field
            "injuries": profile.injuries, # JSONB field
        }

    except ValueError:
        return {"error": "Invalid User ID format. Expected an integer."}
    except Exception as e:
        logger.error(f"Database error retrieving profile: {e}")
        return {"error": "An internal database error occurred."}
    finally:
        db.close() # Always close the connection

def update_user_profile(user_id: str, updated_data: dict):
    """
    Updates specific fields in the real user profile in PostgreSQL.
    """
    db: Session = SessionLocal()
    try:
        uid = int(user_id)
        profile = db.query(Profile).filter(Profile.user_id == uid).first()
        
        if not profile:
            return {"error": "User profile not found to update."}

        # Dynamically update only the fields provided in updated_data
        for key, value in updated_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        db.commit() # Save changes to DB
        logger.info(f"Profile updated successfully for user_id: {uid}")
        return {"status": "success", "message": "Profile updated successfully in database."}

    except ValueError:
        return {"error": "Invalid User ID format."}
    except Exception as e:
        db.rollback() # Rollback if something goes wrong
        logger.error(f"Database error updating profile: {e}")
        return {"error": "Failed to update profile in database."}
    finally:
        db.close()
