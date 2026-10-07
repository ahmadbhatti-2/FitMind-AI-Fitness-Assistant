import hashlib
from itertools import islice, product
import json
from datetime import date
from pathlib import Path

from recommendation.ranking import rank_meals


MEAL_CALORIE_SHARES = {
    "breakfast": 0.25,
    "lunch": 0.30,
    "dinner": 0.30,
    "snack": 0.15,
}
def load_json(filename):
    file_path = Path(__file__).resolve().parent.parent / "data" / filename
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_term(value):
    term = str(value).strip().casefold().replace("_", " ").replace("-", " ")
    term = " ".join(term.split())
    if term.endswith("ies") and len(term) > 3:
        return term[:-3] + "y"
    if term.endswith("s") and not term.endswith("ss") and len(term) > 3:
        return term[:-1]
    return term


def _items(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, (list, tuple, set)):
        return [item for item in value if item is not None]
    return [value]


def _restriction_terms(restrictions):
    terms = set()
    for item in _items(restrictions):
        restriction = str(item).strip().casefold().replace("_", "-").replace(" ", "-")
        if not restriction:
            continue
        term = restriction.removesuffix("-free")
        if term in {"dairy", "lactose"}:
            term = "milk"
        if term in {"nut", "nuts", "tree-nut", "tree-nuts"}:
            terms.update({
                "peanut", "almond", "walnut", "cashew",
                "hazelnut", "pecan", "pistachio",
            })
        else:
            terms.add(normalize_term(term))
    return terms


def _allergy_terms(allergies):
    terms = set()
    aliases = {
        "tree nut": {"almond", "walnut", "cashew", "hazelnut", "pecan", "pistachio"},
        "nut": {"peanut", "almond", "walnut", "cashew", "hazelnut", "pecan", "pistachio"},
        "dairy": {"milk"},
        "lactose": {"milk"},
        "seafood": {"fish", "shellfish", "shrimp"},
    }
    for item in _items(allergies):
        normalized = normalize_term(item)
        terms.add(normalized)
        for alias, foods in aliases.items():
            if alias in normalized:
                terms.update(foods)
    return terms


def _food_is_safe(food, profile):
    if not food:
        return False
    allergies = _allergy_terms(profile.get("allergies"))
    restrictions = _restriction_terms(profile.get("restrictions"))
    allergens = {
        normalize_term(value)
        for value in (_items(food.get("common_allergens")) + _items(food.get("contains")))
    }
    ingredients = {normalize_term(food.get("name") or "")}
    return not (
        allergies.intersection(allergens | ingredients)
        or restrictions.intersection(allergens | ingredients)
    )


def _compatible_diets(diet_preference):
    return {
        "omnivore": {"omnivore", "vegetarian", "vegan"},
        "vegetarian": {"vegetarian", "vegan"},
        "vegan": {"vegan"},
        "pescatarian": {"pescatarian", "vegetarian", "vegan"},
    }.get(str(diet_preference or "omnivore").casefold(), {str(diet_preference).casefold()})


def _food_allowed_for_diet(food, diet_preference):
    diet = str(diet_preference or "omnivore").casefold()
    food_diets = set(food.get("diet_types") or [])
    if diet == "omnivore":
        return True
    if diet == "pescatarian":
        if food.get("category") != "protein":
            return bool(food_diets.intersection({"omnivore", "vegetarian", "vegan", "pescatarian"}))
        contains = {
            normalize_term(value)
            for value in _items(food.get("contains"))
        }
        name = normalize_term(food.get("name") or "")
        land_meats = {"chicken", "beef", "turkey", "pork", "lamb"}
        return not any(meat in contains or meat in name for meat in land_meats)
    required = {"vegan"} if diet == "vegan" else {"vegetarian", "vegan"}
    return bool(food_diets.intersection(required))


def filter_meals(user_profile, meal_type):
    """Filter catalog meal structures against diet, allergens, and dislikes."""
    templates = load_json("meal_templates.json")
    foods = load_json("foods.json")
    food_by_key = {
        food["name"].casefold().replace(" ", "_"): food
        for food in foods
    }
    compatible_diets = _compatible_diets(user_profile.get("diet_preference"))
    goal = str(user_profile.get("goal") or "general_fitness").casefold()
    allergies = _allergy_terms(user_profile.get("allergies"))
    restrictions = _restriction_terms(user_profile.get("restrictions"))
    dislikes = {normalize_term(item) for item in _items(user_profile.get("dislikes"))}

    suitable = []
    goal_matched = []
    for meal in templates:
        if meal.get("meal_type") != meal_type:
            continue
        if not compatible_diets.intersection(meal.get("diet_types") or []):
            continue

        safe = True
        for ingredient in meal.get("ingredients") or []:
            food = food_by_key.get(str(ingredient).casefold())
            if ingredient in {"salad", "vegetables"}:
                continue
            if not food or not _food_is_safe(food, user_profile):
                safe = False
                break
            if not _food_allowed_for_diet(food, user_profile.get("diet_preference")):
                safe = False
                break
            food_allergens = {
                normalize_term(value)
                for value in (_items(food.get("common_allergens")) + _items(food.get("contains")))
            }
            if allergies.intersection(food_allergens) or restrictions.intersection(food_allergens):
                safe = False
                break
        if not safe:
            continue
        if any(normalize_term(item) in dislikes for item in meal.get("ingredients") or []):
            continue
        suitable.append(meal)
        if goal in (meal.get("goal_tags") or []):
            goal_matched.append(meal)
    return goal_matched or suitable


def calculate_daily_targets(profile):
    """Estimate adult energy needs and goal-oriented daily macro targets from profile data."""
    weight = profile.get("weight")
    height = profile.get("height")
    age = profile.get("age")
    if weight is None or height is None or age is None:
        return {
            "calories": None,
            "protein_g": None,
            "carbs_g": None,
            "fat_g": None,
            "calculation_available": False,
            "note": "Add age, height (cm), and weight (kg) to calculate daily nutrition targets.",
        }

    try:
        weight_kg = float(weight)
        height_cm = float(height)
        age_years = int(age)
    except (TypeError, ValueError):
        return {
            "calories": None,
            "protein_g": None,
            "carbs_g": None,
            "fat_g": None,
            "calculation_available": False,
            "note": "Add valid age, height (cm), and weight (kg) to calculate daily nutrition targets.",
        }
    if weight_kg <= 0 or height_cm <= 0 or age_years <= 0:
        return {
            "calories": None,
            "protein_g": None,
            "carbs_g": None,
            "fat_g": None,
            "calculation_available": False,
            "note": "Add valid age, height (cm), and weight (kg) to calculate daily nutrition targets.",
        }
    if age_years < 18:
        return {
            "calories": None,
            "protein_g": None,
            "carbs_g": None,
            "fat_g": None,
            "calculation_available": False,
            "note": "For users under 18, daily calorie and macro targets need guidance from a qualified health professional.",
        }

    sex_adjustment = {"male": 5, "female": -161}.get(
        str(profile.get("gender") or "other").casefold(), -78
    )
    resting_energy = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + sex_adjustment
    try:
        training_days = min(max(int(profile.get("training_days") or 3), 1), 7)
    except (TypeError, ValueError):
        training_days = 3
    activity_factor = min(1.2 + training_days * 0.045, 1.55)
    maintenance = resting_energy * activity_factor
    goal = str(profile.get("goal") or "general_fitness").casefold()
    if goal == "fat_loss":
        energy = maintenance * 0.85
    elif goal == "muscle_gain":
        energy = maintenance * 1.08
    else:
        energy = maintenance

    if age_years >= 18:
        minimum = 1500 if str(profile.get("gender") or "").casefold() == "male" else 1200
        energy = max(energy, minimum)
    calories = round(energy)
    protein_factor = {
        "fat_loss": 2.0,
        "muscle_gain": 1.8,
        "strength": 1.8,
        "general_fitness": 1.6,
    }.get(goal, 1.6)
    protein = round(weight_kg * protein_factor)
    fat = round(max(weight_kg * 0.8, calories * 0.2 / 9))
    carbs = max(0, round((calories - protein * 4 - fat * 9) / 4))
    return {
        "calories": calories,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
        "calculation_available": True,
        "method": "Mifflin-St Jeor estimate adjusted for reported weekly training and goal",
        "note": "Estimates are starting points, not medical advice; actual needs vary.",
    }


def _food_components(meal, foods, profile, seed):
    food_by_key = {food["name"].casefold().replace(" ", "_"): food for food in foods}
    compatible_diets = _compatible_diets(profile.get("diet_preference"))
    allowed = [
        food for food in foods
        if _food_is_safe(food, profile)
        and compatible_diets.intersection(food.get("diet_types") or [])
    ]
    vegetables = sorted(
        (food for food in allowed if food.get("category") == "vegetable"),
        key=lambda food: food["id"],
    )
    components = []
    for ingredient in meal.get("ingredients") or []:
        key = str(ingredient).casefold()
        if key in {"salad", "vegetables"}:
            if not vegetables:
                return []
            start = int(hashlib.sha256(f"{seed}:{meal['id']}:{key}".encode()).hexdigest(), 16) % len(vegetables)
            count = min(2 if key == "salad" else 1, len(vegetables))
            components.extend(vegetables[(start + offset) % len(vegetables)] for offset in range(count))
            continue
        food = food_by_key.get(key)
        if not food or food not in allowed:
            return []
        components.append(food)
    unique = {}
    for food in components:
        unique[food["id"]] = food
    return list(unique.values())


def _dynamic_meals(profile, foods, meal_type, seed):
    """Build fresh food combinations for a meal slot from safe catalog foods."""
    available = [
        food for food in foods
        if meal_type in (food.get("meal_types") or [])
        and _food_is_safe(food, profile)
        and _food_allowed_for_diet(food, profile.get("diet_preference"))
    ]
    proteins = sorted(
        (
            food for food in available
            if food.get("category") != "vegetable"
            and float(food.get("protein_g") or 0) >= 8
        ),
        key=lambda food: (-float(food.get("protein_g") or 0), food["id"]),
    )[:10]
    carbohydrates = sorted(
        (
            food for food in available
            if food.get("category") in {"grain", "fruit", "vegetable", "legume"}
            and float(food.get("carbs_g") or 0) >= 10
        ),
        key=lambda food: (-float(food.get("carbs_g") or 0), food["id"]),
    )[:9]
    vegetables = sorted(
        (food for food in available if food.get("category") == "vegetable"),
        key=lambda food: food["id"],
    )[:8]
    fats = sorted(
        (
            food for food in available
            if food.get("category") in {"fat", "nut", "seed"}
        ),
        key=lambda food: food["id"],
    )[:6]

    combinations = []
    if meal_type in {"lunch", "dinner"} and vegetables:
        combinations = [
            (protein, carbohydrate, vegetable, fat)
            for protein, carbohydrate, vegetable, fat in product(
                proteins, carbohydrates, vegetables, fats or [None]
            )
            if len({protein["id"], carbohydrate["id"], vegetable["id"]}) == 3
            and (fat is None or fat["id"] not in {
                protein["id"], carbohydrate["id"], vegetable["id"]
            })
        ]
    else:
        combinations = [
            (protein, carbohydrate, fat)
            for protein, carbohydrate, fat in product(
                proteins, carbohydrates, fats or [None]
            )
            if protein["id"] != carbohydrate["id"]
            and (fat is None or fat["id"] not in {protein["id"], carbohydrate["id"]})
        ]
    if not combinations:
        return []

    limit = min(80, len(combinations))
    offset = int(hashlib.sha256(f"{seed}:{meal_type}".encode()).hexdigest(), 16) % len(combinations)
    stride = max(1, len(combinations) // limit)
    selected = islice(
        (combinations[(offset + index * stride) % len(combinations)] for index in range(limit)),
        limit,
    )
    goal = str(profile.get("goal") or "general_fitness")
    meals = []
    for combination in selected:
        components = [food for food in combination if food is not None]
        ingredient_keys = [
            food["name"].casefold().replace(" ", "_")
            for food in components
        ]
        identity = hashlib.sha256("|".join(sorted(food["id"] for food in components)).encode()).hexdigest()[:12]
        meals.append({
            "id": f"mix_{meal_type}_{identity}",
            "name": " + ".join(food["name"] for food in components),
            "meal_type": meal_type,
            "ingredients": ingredient_keys,
            "diet_types": [str(profile.get("diet_preference") or "omnivore")],
            "goal_tags": [goal],
            "high_protein": True,
        })
    return meals


def _portion_limits(food):
    category = str(food.get("category") or "").casefold()
    tags = {str(tag).casefold() for tag in food.get("tags") or []}
    if category in {"protein", "soy", "dairy"} or "high_protein" in tags:
        return range(50, 301, 25), 125
    if category in {"grain", "legume"}:
        return range(25, 301, 25), 60
    if category == "vegetable":
        return range(50, 301, 25), 125
    if category in {"fat", "nut", "seed"}:
        return range(5, 46, 5), 10
    return range(25, 301, 25), 100


def _nutrition_for(components, amounts):
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    for food, grams in zip(components, amounts):
        factor = grams / 100
        totals["calories"] += float(food.get("calories_per_100g") or 0) * factor
        totals["protein_g"] += float(food.get("protein_g") or 0) * factor
        totals["carbs_g"] += float(food.get("carbs_g") or 0) * factor
        totals["fat_g"] += float(food.get("fat_g") or 0) * factor
    return totals


def _macro_fit_score(nutrition, targets):
    calorie_target = targets.get("calories")
    if not calorie_target:
        return 0.0
    score = ((nutrition["calories"] - calorie_target) / max(calorie_target, 150)) ** 2
    for macro in ("protein_g", "carbs_g", "fat_g"):
        target = targets.get(macro)
        if target:
            score += ((nutrition[macro] - target) / max(target, 10)) ** 2
    return score


def _optimize_portions(components, targets):
    amounts = [_portion_limits(food)[1] for food in components]
    if not targets.get("calories"):
        return amounts
    for _ in range(3):
        for index, food in enumerate(components):
            candidates = _portion_limits(food)[0]
            best_amount = amounts[index]
            best_score = float("inf")
            for grams in candidates:
                trial = list(amounts)
                trial[index] = grams
                score = _macro_fit_score(_nutrition_for(components, trial), targets)
                if score < best_score:
                    best_score = score
                    best_amount = grams
            amounts[index] = best_amount
    return amounts


def _meal_entry(meal, components, daily_targets, seed):
    portion_targets = {}
    share = MEAL_CALORIE_SHARES[meal["meal_type"]]
    if daily_targets.get("calories"):
        portion_targets["calories"] = daily_targets["calories"] * share
        for macro in ("protein_g", "carbs_g", "fat_g"):
            if daily_targets.get(macro) is not None:
                portion_targets[macro] = daily_targets[macro] * share

    amounts = _optimize_portions(components, portion_targets)
    raw_totals = _nutrition_for(components, amounts)
    portions = []
    for food, grams in zip(components, amounts):
        nutrient = _nutrition_for([food], [grams])
        portions.append({
            "food_id": food["id"],
            "food_name": food["name"],
            "amount_g": grams,
            "calories": round(nutrient["calories"]),
            "protein_g": round(nutrient["protein_g"], 1),
            "carbs_g": round(nutrient["carbs_g"], 1),
            "fat_g": round(nutrient["fat_g"], 1),
        })

    score = int(hashlib.sha256(
        f"{seed}:{meal['id']}".encode()
    ).hexdigest()[:8], 16) / 0xFFFFFFFF * 0.01

    name = meal.get("name", "Personalized meal")
    if any(portion["food_name"].casefold().replace(" ", "_") not in meal.get("ingredients", []) for portion in portions):
        name = f"{name} with personalized vegetables"
    return {
        "id": meal["id"],
        "meal_name": name,
        "meal_type": meal["meal_type"],
        "ingredients": [f"{portion['amount_g']} g {portion['food_name']}" for portion in portions],
        "portions": portions,
        "calories_est": round(raw_totals["calories"]),
        "macros": {
            "protein_g": round(raw_totals["protein_g"], 1),
            "carbs_g": round(raw_totals["carbs_g"], 1),
            "fat_g": round(raw_totals["fat_g"], 1),
        },
        "is_high_protein": raw_totals["protein_g"] >= 20,
        "goal_match": str(daily_targets.get("goal") or "") in (meal.get("goal_tags") or []),
        "goal_tags": meal.get("goal_tags") or [],
        "reasons": [
            f"Portions are estimated from your daily targets and {meal['meal_type']} allocation." if daily_targets.get("calculation_available") else "Ingredients and estimated portions use your diet and food preferences; add body stats to calculate targets.",
            "Calories and macros are calculated from the food catalog per-100 g nutrition data.",
            "Checked against your recorded food preferences and allergen restrictions.",
        ],
        "alternatives": [],
        "score": score,
        "_portion_targets": portion_targets,
    }


def _plan_nutrition(selected):
    return {
        "calories": sum(meal["calories_est"] for meal in selected.values()),
        **{
            macro: sum(meal["macros"][macro] for meal in selected.values())
            for macro in ("protein_g", "carbs_g", "fat_g")
        },
    }


def _daily_fit_score(selected, targets):
    if not targets.get("calories"):
        return 0.0
    totals = _plan_nutrition(selected)
    score = 2 * (
        (totals["calories"] - targets["calories"])
        / max(targets["calories"], 200)
    ) ** 2
    for macro in ("protein_g", "carbs_g", "fat_g"):
        target = targets.get(macro)
        if target:
            score += (
                (totals[macro] - target) / max(target, 15)
            ) ** 2
    return score


def _optimize_daily_portions(selected, foods, targets):
    if not targets.get("calories"):
        return selected
    food_by_id = {food["id"]: food for food in foods}
    amounts = {
        meal_type: [portion["amount_g"] for portion in meal["portions"]]
        for meal_type, meal in selected.items()
    }

    def nutrition_for_amounts(candidate_amounts):
        totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
        for meal_type, meal in selected.items():
            for portion, grams in zip(meal["portions"], candidate_amounts[meal_type]):
                food = food_by_id[portion["food_id"]]
                factor = grams / 100
                for key, field in (
                    ("calories", "calories_per_100g"),
                    ("protein_g", "protein_g"),
                    ("carbs_g", "carbs_g"),
                    ("fat_g", "fat_g"),
                ):
                    totals[key] += float(food.get(field) or 0) * factor
        return totals

    def nutrition_score(candidate_amounts):
        return _macro_fit_score(nutrition_for_amounts(candidate_amounts), targets)

    for _ in range(3):
        for meal_type, meal in selected.items():
            for index, portion in enumerate(meal["portions"]):
                food = food_by_id[portion["food_id"]]
                best_amount = amounts[meal_type][index]
                best_score = float("inf")
                for grams in _portion_limits(food)[0]:
                    trial = {
                        key: list(values) for key, values in amounts.items()
                    }
                    trial[meal_type][index] = grams
                    score = nutrition_score(trial)
                    if score < best_score:
                        best_score = score
                        best_amount = grams
                amounts[meal_type][index] = best_amount

    for meal_type, meal in selected.items():
        portions = []
        for portion, grams in zip(meal["portions"], amounts[meal_type]):
            food = food_by_id[portion["food_id"]]
            nutrient = _nutrition_for([food], [grams])
            portions.append({
                "food_id": food["id"],
                "food_name": food["name"],
                "amount_g": grams,
                "calories": round(nutrient["calories"]),
                "protein_g": round(nutrient["protein_g"], 1),
                "carbs_g": round(nutrient["carbs_g"], 1),
                "fat_g": round(nutrient["fat_g"], 1),
            })
        totals = _nutrition_for(
            [food_by_id[portion["food_id"]] for portion in portions],
            [portion["amount_g"] for portion in portions],
        )
        meal["portions"] = portions
        meal["ingredients"] = [
            f"{portion['amount_g']} g {portion['food_name']}"
            for portion in portions
        ]
        meal["calories_est"] = round(totals["calories"])
        meal["macros"] = {
            macro: round(totals[macro], 1)
            for macro in ("protein_g", "carbs_g", "fat_g")
        }
        meal["is_high_protein"] = totals["protein_g"] >= 20
    return selected


def build_daily_meal_plan(profile, meal_history=None, feedback=None, user_id=""):
    """Choose and portion a complete day of meals against calculated calorie and macro targets."""
    meal_history = meal_history or []
    feedback = feedback or {}
    foods = load_json("foods.json")
    targets = calculate_daily_targets(profile)
    targets["goal"] = str(profile.get("goal") or "general_fitness")
    targets["calculation_available"] = targets.get("calculation_available", False)
    seed = "|".join((
        str(user_id),
        str(profile.get("goal") or ""),
        str(profile.get("diet_preference") or ""),
        str(profile.get("weight") or ""),
        str(profile.get("training_days") or ""),
    ))
    ranked_options = {}
    disliked_meals = set(feedback.get("meals", []))
    for meal_type in MEAL_CALORIE_SHARES:
        candidates = filter_meals(profile, meal_type) + _dynamic_meals(
            profile, foods, meal_type, seed
        )
        recent_history = [
            entry for entry in meal_history
            if entry.get("meal_type") == meal_type and entry.get("food")
        ][:3]
        recent_meals = {
            entry.get("food")
            for entry in recent_history
        }
        fresh_candidates = [
            candidate for candidate in candidates
            if candidate.get("id") not in recent_meals
        ]
        if fresh_candidates:
            candidates = fresh_candidates
        scored = []
        for meal in candidates:
            if meal.get("id") in disliked_meals:
                continue
            components = _food_components(meal, foods, profile, seed)
            if not components:
                continue
            entry = _meal_entry(meal, components, targets, seed)
            entry["goal_match"] = targets["goal"] in entry["goal_tags"]
            if not entry["goal_match"]:
                entry["score"] += 0.5
            scored.append(entry)
        if not scored:
            raise ValueError(
                f"No safe {meal_type} ingredients match the user's diet and allergen restrictions."
            )
        portion_targets = scored[0]["_portion_targets"]
        ranked_options[meal_type] = rank_meals(
            scored,
            profile,
            targets=portion_targets,
            history=[item for item in meal_history if item.get("meal_type") == meal_type],
            feedback=feedback,
        )
    meals = {
        meal_type: options[0]
        for meal_type, options in ranked_options.items()
    }
    for _ in range(2):
        for meal_type, options in ranked_options.items():
            other_meals = {
                key: value for key, value in meals.items() if key != meal_type
            }
            meals[meal_type] = min(
                options[:40],
                key=lambda candidate: (
                    _daily_fit_score(
                        {**other_meals, meal_type: candidate}, targets
                    ),
                    candidate["score"],
                ),
            )

    meals = _optimize_daily_portions(meals, foods, targets)
    for meal_type, selected in meals.items():
        ranked = ranked_options[meal_type]
        alternatives = [
            entry["meal_name"] for entry in ranked
            if entry["id"] != selected["id"]
        ]
        selected["alternatives"] = alternatives[:2]
        selected.pop("score", None)
        selected.pop("_portion_targets", None)
        selected["daily_targets"] = {
            key: value for key, value in targets.items() if key != "goal"
        }
        selected["meal_target"] = {
            "calories": round(targets["calories"] * MEAL_CALORIE_SHARES[meal_type])
            if targets["calories"] else None,
            "protein_g": round(targets["protein_g"] * MEAL_CALORIE_SHARES[meal_type])
            if targets["protein_g"] else None,
            "carbs_g": round(targets["carbs_g"] * MEAL_CALORIE_SHARES[meal_type])
            if targets["carbs_g"] else None,
            "fat_g": round(targets["fat_g"] * MEAL_CALORIE_SHARES[meal_type])
            if targets["fat_g"] else None,
        }

    totals = _plan_nutrition(meals)
    totals["calories"] = round(totals["calories"])
    for macro in ("protein_g", "carbs_g", "fat_g"):
        totals[macro] = round(totals[macro], 1)
    return {
        "type": "daily_meal_plan",
        "date": date.today().isoformat(),
        "daily_targets": {key: value for key, value in targets.items() if key != "goal"},
        "estimated_totals": totals,
        "meals": meals,
        "disclaimer": "Nutrition values are estimates from catalog data and are not medical advice.",
    }


def get_meal_alternatives(food_id):
    """Retrieve substitute foods in the same food category."""
    foods = load_json("foods.json")
    target = next((food for food in foods if food["id"] == food_id), None)
    if not target:
        return []
    return [
        food for food in foods
        if food["category"] == target["category"] and food["id"] != food_id
    ]
