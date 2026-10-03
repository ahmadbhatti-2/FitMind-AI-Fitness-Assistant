def rank_workouts(candidates, user_profile, history):
    """
    Ranks workout candidates by prioritizing direct goal alignment and penalizing recent repetition.
    """
    scored_candidates = []
    user_goal = (user_profile.get('goal') or 'general_fitness').lower()

    for template in candidates:
        score = 0
        
        # Boost weight for templates that directly match the user's primary fitness goal
        if template.get('goal') == user_goal:
            score += 10
        
        # Apply recency penalty to promote workout variety and prevent routine fatigue
        recent_templates = history.get('recent_templates', [])
        if template['id'] in recent_templates:
            score -= 5
            
        scored_candidates.append((template, score))

    # Sort candidates in descending order of calculated relevance score
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Strip score metadata and return ordered list of workout templates
    return [item[0] for item in scored_candidates]

def rank_meals(candidates, user_profile):
    """
    Ranks meal options according to macronutrient priority matching the user's active goal.
    """
    scored_meals = []
    user_goal = (user_profile.get('goal') or 'general_fitness').lower()

    for meal in candidates:
        score = 0
        
        # Prioritize high-protein options to support hyper-trophy and strength adaptations
        if user_goal in ['muscle_gain', 'strength'] and meal.get('high_protein'):
            score += 10
        
        # Heuristic boost for non-high-protein meals under fat loss goal (assumes lower energy density)
        if user_goal == 'fat_loss' and not meal.get('high_protein'): 
            score += 5

        scored_meals.append((meal, score))

    scored_meals.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in scored_meals]