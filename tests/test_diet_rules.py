from recommendation import diet_rules


def test_daily_targets_use_profile_stats_and_goal_adjustment():
	profile = {
		"age": 30,
		"gender": "female",
		"height": 165,
		"weight": 68,
		"goal": "general_fitness",
		"training_days": 4,
	}

	maintenance = diet_rules.calculate_daily_targets(profile)
	fat_loss = diet_rules.calculate_daily_targets({**profile, "goal": "fat_loss"})

	assert maintenance["calculation_available"]
	assert fat_loss["calories"] < maintenance["calories"]
	assert fat_loss["protein_g"] > maintenance["protein_g"]
	assert maintenance["fat_g"] > 0
	assert maintenance["carbs_g"] > 0


def test_daily_targets_are_not_estimated_for_minors_or_missing_body_stats():
	minor = diet_rules.calculate_daily_targets({
		"age": 16, "height": 170, "weight": 60, "goal": "fat_loss",
	})
	incomplete = diet_rules.calculate_daily_targets({"age": 30, "weight": 60})

	assert minor["calories"] is None
	assert not minor["calculation_available"]
	assert incomplete["calories"] is None
	assert not incomplete["calculation_available"]


def test_daily_meal_plan_uses_catalog_macros_portions_and_safe_foods():
	profile = {
		"age": 29,
		"gender": "female",
		"height": 165,
		"weight": 68,
		"goal": "muscle_gain",
		"training_days": 4,
		"diet_preference": "vegan",
		"allergies": ["peanuts"],
		"restrictions": [],
	}

	plan = diet_rules.build_daily_meal_plan(profile, user_id="vegan-member")

	assert set(plan["meals"]) == {"breakfast", "lunch", "dinner", "snack"}
	assert plan["daily_targets"]["calculation_available"]
	assert any(meal["id"].startswith("mix_") for meal in plan["meals"].values())

	foods = {food["id"]: food for food in diet_rules.load_json("foods.json")}
	for meal in plan["meals"].values():
		calories = 0
		protein = 0
		for portion in meal["portions"]:
			food = foods[portion["food_id"]]
			assert "vegan" in food["diet_types"]
			assert "peanut" not in {
				diet_rules.normalize_term(allergen)
				for allergen in food.get("common_allergens", []) + food.get("contains", [])
			}
			factor = portion["amount_g"] / 100
			calories += food["calories_per_100g"] * factor
			protein += food["protein_g"] * factor
		assert meal["calories_est"] == round(calories)
		assert meal["macros"]["protein_g"] == round(protein, 1)
	assert plan["estimated_totals"]["calories"] == sum(
		meal["calories_est"] for meal in plan["meals"].values()
	)
	for nutrient in ("calories", "protein_g", "carbs_g", "fat_g"):
		target = plan["daily_targets"][nutrient]
		actual = plan["estimated_totals"][nutrient]
		assert abs(actual - target) / target <= 0.15, (nutrient, actual, target)


def test_meal_history_and_feedback_change_candidate_selection():
	profile = {
		"age": 30,
		"gender": "male",
		"height": 180,
		"weight": 82,
		"goal": "general_fitness",
		"training_days": 3,
		"diet_preference": "omnivore",
	}
	first = diet_rules.build_daily_meal_plan(profile, user_id="history-member")
	repeated_id = first["meals"]["lunch"]["id"]
	with_history = diet_rules.build_daily_meal_plan(
		profile,
		meal_history=[{"food": repeated_id, "meal_type": "lunch"}] * 6,
		user_id="history-member",
	)

	assert with_history["meals"]["lunch"]["id"] != repeated_id


def test_filter_meals_handles_null_allergies_and_dislikes(monkeypatch):
	meal = {
		"name": "Egg Oat Breakfast",
		"meal_type": "breakfast",
		"diet_types": ["omnivore"],
		"goal_tags": ["muscle_gain"],
		"ingredients": ["eggs", "oats"],
	}
	foods = [
		{"name": "Eggs", "diet_types": ["omnivore", "vegetarian"], "common_allergens": [], "contains": []},
		{"name": "Oats", "diet_types": ["omnivore", "vegetarian", "vegan"], "common_allergens": [], "contains": []},
	]
	data = {"meal_templates.json": [meal], "foods.json": foods}
	monkeypatch.setattr(diet_rules, "load_json", lambda filename: data[filename])

	result = diet_rules.filter_meals(
		{
			"diet_preference": "omnivore",
			"goal": "muscle_gain",
			"allergies": None,
			"dislikes": None,
		},
		"breakfast",
	)

	assert result == [meal]


def test_filter_meals_blocks_plural_allergies_and_free_from_restrictions(monkeypatch):
	meal = {
		"id": "breakfast",
		"name": "Egg Oat Breakfast",
		"meal_type": "breakfast",
		"diet_types": ["omnivore"],
		"goal_tags": ["muscle_gain"],
		"ingredients": ["eggs", "oats"],
	}
	foods = [
		{
			"name": "Eggs",
			"common_allergens": ["egg"],
			"contains": ["egg"],
		},
		{
			"name": "Oats",
			"common_allergens": ["gluten"],
			"contains": ["gluten"],
		},
	]
	data = {"meal_templates.json": [meal], "foods.json": foods}
	monkeypatch.setattr(diet_rules, "load_json", lambda filename: data[filename])
	profile = {
		"diet_preference": "omnivore",
		"goal": "muscle_gain",
		"allergies": ["eggs"],
		"restrictions": [],
	}

	assert diet_rules.filter_meals(profile, "breakfast") == []

	profile["allergies"] = []
	profile["restrictions"] = ["gluten-free"]
	assert diet_rules.filter_meals(profile, "breakfast") == []


def test_meal_filter_uses_safe_fallback_goal_and_excludes_eggs_for_vegan(monkeypatch):
	meal = {
		"name": "Lentil Roti Bowl",
		"meal_type": "lunch",
		"diet_types": ["vegetarian", "vegan"],
		"goal_tags": ["general_fitness"],
		"ingredients": ["lentils"],
	}
	egg_meal = {
		"name": "Egg Oat Breakfast",
		"meal_type": "breakfast",
		"diet_types": ["omnivore", "vegetarian"],
		"goal_tags": ["general_fitness"],
		"ingredients": ["eggs"],
	}
	foods = [
		{"name": "Lentils", "diet_types": ["omnivore", "vegetarian", "vegan"], "common_allergens": [], "contains": []},
		{"name": "Eggs", "diet_types": ["omnivore", "vegetarian"], "common_allergens": [], "contains": []},
	]
	data = {"meal_templates.json": [meal, egg_meal], "foods.json": foods}
	monkeypatch.setattr(diet_rules, "load_json", lambda filename: data[filename])

	assert diet_rules.filter_meals(
		{"goal": "strength", "diet_preference": "vegan"},
		"lunch",
	) == [meal]
	assert diet_rules.filter_meals(
		{"goal": "general_fitness", "diet_preference": "vegan"},
		"breakfast",
	) == []


def test_catalog_has_a_safe_option_for_every_supported_goal_and_meal_type():
	for goal in ("general_fitness", "muscle_gain", "fat_loss", "strength"):
		for diet in ("omnivore", "vegetarian", "vegan", "pescatarian"):
			profile = {"goal": goal, "diet_preference": diet}
			for meal_type in ("breakfast", "lunch", "dinner", "snack"):
				assert diet_rules.filter_meals(profile, meal_type), (goal, diet, meal_type)
