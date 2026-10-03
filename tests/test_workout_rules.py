from recommendation import workout_rules


def test_template_selection_respects_recovery_equipment_and_recent_workouts(monkeypatch):
    templates = [
        {
            "id": "push",
            "goal": "general_fitness",
            "experience": "beginner",
            "equipment": ["bodyweight"],
            "muscle_groups": ["chest", "shoulders"],
            "template_exercises": [],
        },
        {
            "id": "pull",
            "goal": "general_fitness",
            "experience": "beginner",
            "equipment": ["bodyweight", "dumbbells"],
            "muscle_groups": ["back"],
            "template_exercises": [],
        },
        {
            "id": "barbell",
            "goal": "general_fitness",
            "experience": "beginner",
            "equipment": ["barbell"],
            "muscle_groups": ["legs"],
            "template_exercises": [],
        },
    ]
    monkeypatch.setattr(workout_rules, "load_json", lambda _: templates)

    result = workout_rules.get_recommended_template(
        {
            "goal": "general_fitness",
            "experience": "beginner",
            "equipment": ["bodyweight"],
        },
        {
            "last_muscle_group": "chest",
            "recent_template_ids": ["pull"],
            "recovery_required": True,
        },
    )

    assert result is None

    result = workout_rules.get_recommended_template(
        {
            "goal": "general_fitness",
            "experience": "beginner",
            "equipment": ["bodyweight"],
        },
        {"last_muscle_group": "chest", "recent_template_ids": []},
    )
    assert result["id"] == "pull"


def test_exercise_filter_enforces_equipment_injuries_and_experience():
    exercises = [
        {
            "id": "safe",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "injury_caution": [],
        },
        {
            "id": "injury",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "injury_caution": ["shoulder"],
        },
        {
            "id": "equipment",
            "equipment": ["barbell"],
            "difficulty": "beginner",
            "injury_caution": [],
        },
        {
            "id": "advanced",
            "equipment": ["bodyweight"],
            "difficulty": "advanced",
            "injury_caution": [],
        },
    ]

    result = workout_rules.filter_exercises_by_context(
        exercises,
        {
            "equipment": ["bodyweight"],
            "experience": "beginner",
            "injuries": ["shoulder pain"],
        },
    )

    assert [exercise["id"] for exercise in result] == ["safe"]


def test_template_selection_falls_back_to_a_safe_available_experience(monkeypatch):
    templates = [
        {
            "id": "general-beginner",
            "goal": "general_fitness",
            "experience": "beginner",
            "equipment": ["bodyweight"],
            "muscle_groups": ["legs"],
            "template_exercises": [],
        },
        {
            "id": "strength-advanced",
            "goal": "strength",
            "experience": "advanced",
            "equipment": ["bodyweight"],
            "muscle_groups": ["chest"],
            "template_exercises": [],
        },
    ]
    monkeypatch.setattr(workout_rules, "load_json", lambda _: templates)

    result = workout_rules.get_recommended_template(
        {
            "goal": "general_fitness",
            "experience": "advanced",
            "equipment": ["bodyweight"],
        },
        {"last_muscle_group": None},
    )

    assert result["id"] == "general-beginner"
    assert result["goal_match"]
    assert not result["experience_match"]


def test_template_selection_does_not_repeat_recovery_groups_too_soon(monkeypatch):
    templates = [
        {
            "id": "full-body",
            "goal": "general_fitness",
            "experience": "beginner",
            "equipment": ["bodyweight"],
            "muscle_groups": ["chest", "legs"],
            "template_exercises": [],
        },
    ]
    monkeypatch.setattr(workout_rules, "load_json", lambda _: templates)

    result = workout_rules.get_recommended_template(
        {
            "goal": "general_fitness",
            "experience": "beginner",
            "equipment": ["bodyweight"],
        },
        {"last_muscle_group": "chest, legs", "recovery_required": True},
    )

    assert result is None