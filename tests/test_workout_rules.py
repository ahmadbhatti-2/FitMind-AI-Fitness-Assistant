from datetime import date

from recommendation import recovery_rules, workout_rules


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
    assert result["id"] == "push"


def test_exercise_equipment_requires_every_non_bodyweight_item():
    exercises = [
        {
            "id": "needs-bench",
            "equipment": ["bodyweight", "bench"],
            "difficulty": "beginner",
            "injury_caution": [],
        },
        {
            "id": "bodyweight",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "injury_caution": [],
        },
    ]

    assert [
        exercise["id"]
        for exercise in workout_rules.filter_exercises_by_context(
            exercises,
            {"equipment": ["bodyweight"], "experience": "beginner"},
        )
    ] == ["bodyweight"]
    assert [
        exercise["id"]
        for exercise in workout_rules.filter_exercises_by_context(
            exercises,
            {"equipment": ["bench"], "experience": "beginner"},
        )
    ] == ["needs-bench", "bodyweight"]


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


def test_severe_injury_context_blocks_related_groups_without_catalog_caution():
    exercises = [{
        "id": "knee-extension",
        "muscle_group": "legs",
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "injury_caution": [],
    }]

    assert workout_rules.filter_exercises_by_context(
        exercises,
        {
            "equipment": ["bodyweight"],
            "experience": "beginner",
            "injuries": ["knee severe pain while bending"],
        },
    ) == []


def test_progression_uses_logged_volume_reps_load_and_effort():
    exercise = {"id": "ex_001"}
    profile = {"goal": "muscle_gain", "experience": "intermediate"}

    result = workout_rules._prescription(
        exercise,
        profile,
        [{
            "performance": {
                "ex_001": {
                    "sets": 3,
                    "reps": 12,
                    "weight_kg": 40,
                    "effort": "easy",
                }
            }
        }],
    )

    assert result["sets"] == 4
    assert result["weight_kg"] == 42
    assert "42 kg" in result["progression"]


def test_recovery_window_changes_with_group_effort_and_recent_volume():
    easy_accessory = recovery_rules.required_recovery_hours(
        "biceps", {"age": 25}, recent_sessions=1, difficulty="easy"
    )
    older_hard_chest = recovery_rules.required_recovery_hours(
        "chest", {"age": 65}, recent_sessions=3, difficulty="hard"
    )

    assert easy_accessory == 24
    assert older_hard_chest > easy_accessory
    assert not recovery_rules.calculate_recovery_window(
            date.today().isoformat(),
            "chest",
            profile={"age": 65},
            recent_sessions=3,
            difficulty="hard",
        )[0]


def test_generated_week_uses_profile_days_and_personalizes_exercises():
    profile = {
        "goal": "strength",
        "experience": "beginner",
        "training_days": 3,
        "equipment": ["bodyweight"],
        "injuries": [],
    }

    first = workout_rules.generate_weekly_workout_plan(profile, [], "member-a")
    second = workout_rules.generate_weekly_workout_plan(profile, [], "member-b")

    assert len(first) == 7
    assert sum(not day["is_rest_day"] for day in first) == 3
    assert all(
        exercise["equipment"] == ["bodyweight"]
        for day in first
        for exercise in day["exercises"]
    )
    first_ids = [
        exercise["id"] for day in first for exercise in day["exercises"]
    ]
    second_ids = [
        exercise["id"] for day in second for exercise in day["exercises"]
    ]
    assert first_ids != second_ids
    assert [
        day["id"] for day in first if not day["is_rest_day"]
    ] != [
        day["id"] for day in second if not day["is_rest_day"]
    ]