import json
from pathlib import Path

def load_json(filename):
    file_path = Path(__file__).resolve().parent.parent / 'data' / filename
    with open(file_path, 'r') as f:
        return json.load(f)

def filter_exercises_by_context(exercises, user_profile):
    """
    Filters exercises based on equipment compatibility, experience level, and medical contraindications.
    """
    user_equipment = {str(item).strip().casefold() for item in (user_profile.get('equipment') or ['bodyweight'])}
    user_experience = (user_profile.get('experience') or 'beginner').casefold()
    experience_levels = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
    user_level = experience_levels.get(user_experience, 0)
    injuries = user_profile.get('injuries') or []
    if isinstance(injuries, str):
        injuries = injuries.split(',')
    user_injuries = {str(item).strip().casefold() for item in injuries if str(item).strip()}

    filtered = []
    for ex in exercises:
        # Exclude exercises that risk worsening existing user injuries
        cautions = {str(item).strip().casefold() for item in ex.get('injury_caution', [])}
        if any(
            caution in injury or injury in caution
            for injury in user_injuries
            for caution in cautions
        ):
            continue

        # Ensure user possesses at least one required piece of equipment for this exercise
        if not any(str(eq).casefold() in user_equipment for eq in ex.get('equipment', [])):
            continue

        # Prevent novice users from receiving high-risk advanced movements
        exercise_level = experience_levels.get(
            str(ex.get('difficulty', 'beginner')).casefold(),
            experience_levels['beginner'],
        )
        if exercise_level > user_level:
            continue

        filtered.append(ex)
    
    return filtered

def get_recommended_template(user_profile, history):
    """
    Selects the optimal workout template using user profile constraints and recent muscle group history.
    """
    templates = load_json('workout_templates.json')
    user_goal = (user_profile.get('goal') or 'general_fitness').casefold()
    user_exp = (user_profile.get('experience') or 'beginner').casefold()
    experience_levels = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
    user_level = experience_levels.get(user_exp, 0)
    user_equipment = {
        str(item).strip().casefold()
        for item in (user_profile.get('equipment') or ['bodyweight'])
    }
    
    last_muscles = {
        item.strip().casefold()
        for item in str(history.get('last_muscle_group') or '').split(',')
        if item.strip()
    }
    recent_template_ids = set(history.get('recent_template_ids') or [])

    # Strict matching for exact user target goals and experience criteria
    suitable_templates = [
        t for t in templates
        if experience_levels.get(str(t['experience']).casefold(), 99) <= user_level
        and user_equipment.intersection(
            str(item).casefold() for item in (t.get('equipment') or [])
        )
    ]

    if not suitable_templates:
        return None

    available = [t for t in suitable_templates if t['id'] not in recent_template_ids]
    if not available:
        return None

    recovery_safe = [
        t for t in available
        if not last_muscles.intersection(group.casefold() for group in t['muscle_groups'])
    ]
    if recovery_safe:
        available = recovery_safe
    elif history.get('recovery_required', False):
        return None

    available.sort(
        key=lambda template: (
            template['goal'] == user_goal,
            template['experience'] == user_exp,
            experience_levels.get(template['experience'], 0),
        ),
        reverse=True,
    )
    recommendation = dict(available[0])
    recommendation['goal_match'] = recommendation['goal'] == user_goal
    recommendation['experience_match'] = recommendation['experience'] == user_exp
    return recommendation

def map_template_to_exercises(template_id):
    """
    Hydrates template exercise ID references into full exercise data models.
    """
    exercises = load_json('exercises.json')
    templates = load_json('workout_templates.json')
    
    # Locate target template by unique identifier
    template = next((t for t in templates if t['id'] == template_id), None)
    if not template:
        return []

    # Cross-reference exercise IDs to retrieve full entity detail maps
    return [ex for ex in exercises if ex['id'] in template['template_exercises']]