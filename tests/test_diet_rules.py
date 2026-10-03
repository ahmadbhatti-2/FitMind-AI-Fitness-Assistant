from recommendation import diet_rules


def test_filter_meals_handles_null_allergies_and_dislikes(monkeypatch):
	meal = {
		"name": "Egg Oat Breakfast",
		"meal_type": "breakfast",
		"diet_types": ["omnivore"],
		"goal_tags": ["muscle_gain"],
		"ingredients": ["eggs", "oats"],
	}
	data = {"meal_templates.json": [meal], "foods.json": []}
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
	data = {"meal_templates.json": [meal, egg_meal], "foods.json": []}
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
