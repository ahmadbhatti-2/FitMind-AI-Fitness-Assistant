import logging
from agent.tools.user_tool import get_user_profile
from agent.tools.history_tool import get_meal_history
from agent.tools.feedback_tool import get_user_feedback_summary
from recommendation import diet_rules, ranking

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recommend_meal(user_id: str, meal_type: str):
    """
    Generates a safe meal recommendation using database profile context and meal history logs.
    """
    try:
        # Halt execution if user profile lookup returns an error payload
        profile = get_user_profile(user_id)
        if isinstance(profile, dict) and "error" in profile:
            return profile

        history = get_meal_history(user_id)
        if isinstance(history, dict) and "error" in history:
            return history
        feedback = get_user_feedback_summary(user_id)
        if isinstance(feedback, dict) and "error" in feedback:
            return feedback

        # Filter options based on safety constraints and dietary preferences
        suitable_meals = diet_rules.filter_meals(profile, meal_type)
        disliked_meals = set(feedback.get("meals", []))
        suitable_meals = [meal for meal in suitable_meals if meal["id"] not in disliked_meals]

        if not suitable_meals:
            return {"error": f"No suitable {meal_type} found for your real diet preferences."}

        # Rank meals by fitness goal alignment
        ranked_meals = ranking.rank_meals(suitable_meals, profile)
        best_meal = ranked_meals[0]

        # Fallback to second best option if top choice was logged in recent history
        recent_meals = {h.get('food') for h in history[:2]}
        alternative = next(
            (meal for meal in ranked_meals if meal["id"] not in recent_meals),
            best_meal,
        )
        best_meal = alternative

        # Format and return structured recommendation response
        goal_match = profile.get("goal") in best_meal.get("goal_tags", [])
        return {
            "type": "meal_recommendation",
            "id": best_meal["id"],
            "goal_match": goal_match,
            "meal_name": best_meal['name'],
            "meal_type": meal_type,
            "ingredients": best_meal['ingredients'],
            "is_high_protein": best_meal.get('high_protein', False),
            "reasons": [
                f"Matches your {profile.get('diet_preference', 'omnivore')} diet",
                (
                    f"Matches your {profile.get('goal', 'fitness')} goal"
                    if goal_match
                    else f"No catalog meal is tagged for {profile.get('goal', 'fitness')} and {meal_type}; this option still fits your recorded diet and avoids listed allergens"
                ),
                "Safe for your recorded allergies"
            ],
            "alternatives": [m['name'] for m in ranked_meals[1:3]]
        }

    except Exception as e:
        # Mask database/pipeline errors from client response
        logger.error(f"Real DB Diet Error: {e}")
        return {"error": "An internal error occurred while generating the real meal plan."}

def get_food_replacement(food_id: str):
    """
    Retrieves substitute options belonging to the same food category.
    """
    try:
        alternatives = diet_rules.get_meal_alternatives(food_id)
        if not alternatives:
            return {"error": "No suitable alternatives found."}
            
        # Limit replacement suggestions to top 3 choices
        return {
            "original_food_id": food_id,
            "alternatives": [alt['name'] for alt in alternatives[:3]]
        }
    except Exception as e:
        logger.error(f"Error getting real food replacement: {e}")
        return {"error": "Failed to fetch food alternatives."}