import json
from pathlib import Path

def load_json(filename):
    file_path = Path(__file__).resolve().parent.parent / 'data' / filename
    with open(file_path, 'r') as f:
        return json.load(f)

def normalize_term(value):
        term = str(value).strip().casefold()
        if term.endswith("ies") and len(term) > 3:
            return term[:-3] + "y"
        if term.endswith("s") and not term.endswith("ss") and len(term) > 3:
            return term[:-1]
        return term

def filter_meals(user_profile, meal_type):
    """
    Filters meal options matching user dietary guidelines, fitness goals, and medical safety restrictions.
    """
    templates = load_json('meal_templates.json')
    foods = load_json('foods.json')
    
    diet_pref = (user_profile.get('diet_preference') or 'omnivore').casefold()
    goal = (user_profile.get('goal') or 'general_fitness').casefold()
    allergies = user_profile.get('allergies') or []
    if isinstance(allergies, str):
        allergies = allergies.split(',')
    allergies = {normalize_term(item) for item in allergies if str(item).strip()}
    dislikes = user_profile.get('dislikes') or []
    if isinstance(dislikes, str):
        dislikes = dislikes.split(',')
    dislikes = {normalize_term(item) for item in dislikes if str(item).strip()}
    restrictions = user_profile.get('restrictions') or []
    if isinstance(restrictions, str):
        restrictions = restrictions.split(',')
    restriction_terms = set()
    for item in restrictions:
        restriction = str(item).strip().casefold().replace('_', '-')
        if not restriction:
            continue
        term = restriction.removesuffix('-free')
        if term in {'dairy', 'lactose'}:
            term = 'milk'
        if term in {'nut', 'nuts'}:
            restriction_terms.update({'peanut', 'almond', 'walnut', 'cashew'})
        else:
            restriction_terms.add(normalize_term(term))

    suitable_meals = []
    goal_matched_meals = []
    compatible_diets = {
        'omnivore': {'omnivore', 'vegetarian', 'vegan'},
        'vegetarian': {'vegetarian', 'vegan'},
        'vegan': {'vegan'},
        'pescatarian': {'pescatarian', 'vegetarian', 'vegan'},
    }.get(diet_pref, {diet_pref})

    for meal in templates:
        if meal['meal_type'] != meal_type or not compatible_diets.intersection(meal['diet_types']):
            continue

        # Strict safety check: exclude meals containing ingredients with flagged user allergens
        is_safe = True
        for ingredient in meal['ingredients']:
            # Normalize ingredient string format for uniform matching against master food database
            food_item = next((f for f in foods if f['name'].lower().replace(" ", "_") == ingredient.lower()), None)
            
            food_allergens = {
                normalize_term(allergen)
                for allergen in (
                    (food_item.get('common_allergens') or [])
                    + (food_item.get('contains') or [])
                )
            } if food_item else set()
            food_contains = {
                normalize_term(component)
                for component in (food_item.get('contains') or [])
            } if food_item else set()
            ingredient_term = normalize_term(ingredient)
            if (
                allergies.intersection(food_allergens)
                or restriction_terms.intersection(food_allergens | food_contains | {ingredient_term})
            ):
                is_safe = False
                break
        
        if not is_safe:
            continue

        # Soft constraint: exclude meals containing explicitly disliked items
        normalized_ingredients = {normalize_term(ingredient) for ingredient in meal['ingredients']}
        if dislikes.intersection(normalized_ingredients):
            continue

        suitable_meals.append(meal)
        if goal in meal['goal_tags']:
            goal_matched_meals.append(meal)

    return goal_matched_meals or suitable_meals

def get_meal_alternatives(food_id):
    """
    Retrieves substitute foods belonging to the same nutritional category.
    """
    foods = load_json('foods.json')
    target_food = next((f for f in foods if f['id'] == food_id), None)
    
    # Return empty fallback if target food record is missing
    if not target_food:
        return []

    category = target_food['category']
    
    # Query substitute ingredients within the same category while excluding the original item
    return [f for f in foods if f['category'] == category and f['id'] != food_id]