import hashlib


def rank_workouts(candidates, user_profile, history, user_id=""):
    """
    Rank safe exercise candidates by goal, experience, performance history, and member variety.
    """
    scored_candidates = []
    user_goal = (user_profile.get('goal') or 'general_fitness').lower()
    user_experience = str(user_profile.get("experience") or "beginner").casefold()
    experience_levels = {"beginner": 0, "intermediate": 1, "advanced": 2}
    history_entries = history if isinstance(history, list) else []
    performance_history = [
        entry.get("performance") or {}
        for entry in history_entries[:5]
        if isinstance(entry.get("performance"), dict)
    ]

    for exercise in candidates:
        score = 0.0
        if user_goal not in (exercise.get("goal_tags") or []):
            score += 2
        exercise_level = experience_levels.get(
            str(exercise.get("difficulty") or "beginner").casefold(), 0
        )
        score += abs(experience_levels.get(user_experience, 0) - exercise_level) * 0.5
        previous_sessions = sum(
            1 for record in performance_history if exercise.get("id") in record
        )
        score += previous_sessions * 2
        score += int(hashlib.sha256(
            f"{user_id}:{exercise.get('id', '')}".encode()
        ).hexdigest()[:8], 16) / 0xFFFFFFFF * 0.001
        scored_candidates.append((exercise, score))

    scored_candidates.sort(key=lambda item: item[1])
    return [item[0] for item in scored_candidates]

def rank_meals(candidates, user_profile, targets=None, history=None, feedback=None):
    """
    Ranks measured meal candidates by goal fit, macro fit, variety, and user feedback.
    """
    targets = targets or {}
    history = history or []
    feedback = feedback or {}
    scored_meals = []
    user_goal = (user_profile.get('goal') or 'general_fitness').lower()

    for meal in candidates:
        score = float(meal.get("score", 0))

        if user_goal in meal.get("goal_tags", []):
            score -= 0.5
        nutrition = meal.get("macros") or {}
        for macro in ("protein_g", "carbs_g", "fat_g"):
            target = targets.get(macro)
            if target:
                score += ((nutrition.get(macro, 0) - target) / max(target, 10)) ** 2
        calorie_target = targets.get("calories")
        if calorie_target:
            score += ((meal.get("calories_est", 0) - calorie_target) / max(calorie_target, 150)) ** 2

        if meal.get("id") in feedback.get("meals", []):
            score += 100
        history_count = sum(1 for item in history if item.get("food") == meal.get("id"))
        if meal.get("id") in {item.get("food") for item in history[:5]}:
            score += 8
        score += min(history_count, 10) * 1.5

        scored_meals.append((meal, score))

    scored_meals.sort(key=lambda x: x[1])
    return [item[0] for item in scored_meals]