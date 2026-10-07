import logging

from agent.tools.feedback_tool import get_user_feedback_summary
from agent.tools.history_tool import get_workout_history
from agent.tools.user_tool import get_user_profile
from recommendation import workout_rules


logger = logging.getLogger(__name__)


def recommend_workout(user_id: str):
    """Build a goal-, equipment-, recovery-, and performance-aware workout week."""
    try:
        profile = get_user_profile(user_id)
        if isinstance(profile, dict) and "error" in profile:
            return profile

        history = get_workout_history(user_id)
        if isinstance(history, dict) and "error" in history:
            return history
        feedback = get_user_feedback_summary(user_id)
        if isinstance(feedback, dict) and "error" in feedback:
            return feedback
        recommendation = workout_rules.generate_workout(
            profile,
            history,
            user_id,
            feedback.get("workouts", []),
        )
        if not recommendation.get("exercises") and not recommendation.get("is_recovery_day"):
            return {
                "error": "No safe exercises match your equipment, experience, injury notes, and current recovery needs. Review your profile or seek professional guidance."
            }
        return recommendation
    except Exception:
        logger.exception("Workout recommendation failed for user %s", user_id)
        return {"error": "An internal error occurred while generating the workout."}
