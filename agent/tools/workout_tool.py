import logging
from datetime import date
from agent.tools.user_tool import get_user_profile
from agent.tools.history_tool import get_workout_history, get_last_trained_muscle
from recommendation import recovery_rules, workout_rules

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recommend_workout(user_id: str):
    """
    Generates a personalized workout recommendation using database context and safety constraints.
    """
    try:
        # Halt early if user profile lookup fails
        profile = get_user_profile(user_id)
        if isinstance(profile, dict) and "error" in profile:
            return profile

        history = get_workout_history(user_id)
        if isinstance(history, dict) and "error" in history:
            return history
        last_muscle = get_last_trained_muscle(user_id)
        last_completed = next(
            (item for item in history if item.get("status") == "completed"),
            None,
        )
        recovered, recovery_message = (
            recovery_rules.calculate_recovery_window(
                last_completed["date"], last_muscle
            )
            if last_completed
            else (True, "No previous completed workout is logged.")
        )

        # Resolve workout template matching profile preferences and recent history
        history_context = {
            "last_muscle_group": last_muscle,
            "recent_template_ids": [
                item.get("template_id")
                for item in history
                if item.get("status") == "completed"
                and item.get("template_id")
                and date.fromisoformat(item["date"]) == date.today()
            ],
            "recovery_required": not recovered,
        }
        template = workout_rules.get_recommended_template(profile, history_context)

        if not template:
            if not recovered:
                return {
                    "type": "recovery_recommendation",
                    "id": "recovery_day",
                    "recommended_for": date.today().isoformat(),
                    "is_recovery_day": True,
                    "title": "Recovery day",
                    "duration_minutes": 30,
                    "difficulty": "easy",
                    "muscle_groups": [],
                    "exercises": [{
                        "id": "recovery_walk",
                        "name": "Easy walk or gentle mobility",
                        "sets": 1,
                        "reps": "20–30 minutes at a comfortable pace",
                        "rest": "Stop if anything hurts",
                    }],
                    "reasons": [recovery_message],
                    "safety_note": "Keep the activity light. Stop if you feel pain; this is not medical advice.",
                }
            return {"error": "No workout matches your goal, experience, equipment, and recent history. Update your profile or record."}

        # Map template exercise references to full entity details
        exercises = workout_rules.map_template_to_exercises(template['id'])
        safe_exercises = workout_rules.filter_exercises_by_context(exercises, profile)
        if not safe_exercises:
            return {"error": "No exercises in this workout match your available equipment and recorded injury restrictions."}

        # Format structured recommendation response for client UI
        return {
            "type": "workout_recommendation",
            "id": template['id'],
            "recommended_for": date.today().isoformat(),
            "title": template['name'],
            "duration_minutes": template['duration_minutes'],
            "difficulty": template['experience'],
            "goal_match": template['goal_match'],
            "experience_match": template['experience_match'],
            "muscle_groups": template['muscle_groups'],
            "exercises": safe_exercises,
            "reasons": [
                (
                    f"Matches your {profile.get('goal', 'fitness')} goal and {profile.get('experience', 'beginner')} experience"
                    if template['goal_match'] and template['experience_match']
                    else "Uses the closest available catalog plan that stays within your experience and equipment"
                ),
                f"Prioritizes recovery from your last trained muscle groups ({last_muscle})" if last_muscle else "No previous workout is logged",
                "Uses available equipment and excludes exercises flagged for your recorded injuries"
            ],
            "safety_note": "All exercises filtered based on your database injury profile."
        }

    except Exception as e:
        # Mask database/pipeline errors from client response
        logger.error(f"Real DB Workout Error: {e}")
        return {"error": "An internal error occurred while generating the real workout."}