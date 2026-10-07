import logging

from agent.tools.feedback_tool import get_user_feedback_summary
from agent.tools.history_tool import get_meal_history
from agent.tools.user_tool import get_user_profile
from recommendation import diet_rules


logger = logging.getLogger(__name__)


def recommend_daily_meal_plan(user_id: str):
    """Build one complete day of safe, portioned meals using a member's nutrition targets."""
    try:
        profile = get_user_profile(user_id)
        if isinstance(profile, dict) and "error" in profile:
            return profile
        history = get_meal_history(user_id)
        if isinstance(history, dict) and "error" in history:
            return history
        feedback = get_user_feedback_summary(user_id)
        if isinstance(feedback, dict) and "error" in feedback:
            return feedback
        return diet_rules.build_daily_meal_plan(
            profile,
            meal_history=history,
            feedback=feedback,
            user_id=user_id,
        )
    except ValueError as error:
        logger.info("No meal plan could be built for user %s: %s", user_id, error)
        return {"error": str(error)}
    except Exception:
        logger.exception("Meal plan generation failed for user %s", user_id)
        return {"error": "An internal error occurred while generating the meal plan."}


def recommend_meal(user_id: str, meal_type: str):
    """Return the selected meal from the user's calculated full-day plan."""
    plan = recommend_daily_meal_plan(user_id)
    if isinstance(plan, dict) and "error" in plan:
        return plan
    meal = plan.get("meals", {}).get(meal_type)
    if meal is None:
        return {"error": f"No {meal_type} is available in the generated daily meal plan."}
    return meal


def get_food_replacement(food_id: str):
    """Retrieve food alternatives in the same nutrition category."""
    try:
        alternatives = diet_rules.get_meal_alternatives(food_id)
        if not alternatives:
            return {"error": "No suitable alternatives found."}
        return {
            "original_food_id": food_id,
            "alternatives": [food["name"] for food in alternatives[:3]],
        }
    except Exception:
        logger.exception("Unable to retrieve food alternatives for %s", food_id)
        return {"error": "Failed to fetch food alternatives."}
