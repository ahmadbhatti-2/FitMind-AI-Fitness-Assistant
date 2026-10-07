import json
from datetime import date, timedelta
import hashlib
from pathlib import Path

from recommendation import recovery_rules
from recommendation.ranking import rank_workouts

EXPERIENCE_LEVELS = {"beginner": 0, "intermediate": 1, "advanced": 2}
MUSCLE_GROUPS = {
    "upper": ("chest", "back", "shoulders", "biceps", "triceps", "forearms"),
    "lower": ("legs", "glutes", "calves"),
    "push": ("chest", "shoulders", "triceps"),
    "pull": ("back", "biceps", "forearms"),
    "legs": ("legs", "glutes", "calves"),
    "full_body": ("chest", "back", "legs", "shoulders", "glutes", "core"),
}


def load_json(filename):
    file_path = Path(__file__).resolve().parent.parent / "data" / filename
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def _as_items(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, (list, tuple, set)):
        return [item for item in value if item is not None]
    return [value]


def _equipment_set(profile):
    equipment = {str(item).strip().casefold().replace(" ", "_") for item in _as_items(profile.get("equipment"))}
    equipment.add("bodyweight")
    return equipment


def _injury_entries(profile):
    entries = []
    for item in _as_items(profile.get("injuries")):
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("site") or item.get("injury") or "").strip().casefold()
            severity = str(item.get("severity") or "moderate").strip().casefold()
            context = str(item.get("context") or "").strip().casefold()
            if name:
                entries.append((name, severity, context))
        else:
            text = str(item).strip().casefold()
            if not text:
                continue
            severity = next(
                (level for level in ("acute", "severe", "high", "moderate", "mild", "low") if level in text),
                "moderate",
            )
            entries.append((text, severity, text))
    return entries


def _injury_matches(caution, injury_name, context):
    caution = caution.replace("_", " ").casefold()
    terms = f"{injury_name} {context}".replace("_", " ").casefold()
    if not caution:
        return False
    return caution in terms or terms in caution or any(
        token in terms.split() for token in caution.split() if len(token) > 3
    )


def _severe_injury_affects_group(muscle_group, injury_name, context):
    region_groups = {
        "knee": {"legs", "glutes", "calves"},
        "ankle": {"legs", "glutes", "calves"},
        "hip": {"legs", "glutes"},
        "shoulder": {"chest", "shoulders", "triceps"},
        "elbow": {"biceps", "triceps", "forearms"},
        "back": {"back", "core", "legs"},
        "spine": {"back", "core", "legs"},
        "wrist": {"forearms", "biceps"},
    }
    terms = f"{injury_name} {context}".replace("_", " ").casefold()
    return any(
        region in terms and (muscle_group in groups or muscle_group == "full_body")
        for region, groups in region_groups.items()
    )


def filter_exercises_by_context(exercises, user_profile):
    """Keep only movements the user can perform safely with all required equipment."""
    user_equipment = _equipment_set(user_profile)
    user_level = EXPERIENCE_LEVELS.get(
        str(user_profile.get("experience") or "beginner").casefold(), 0
    )
    injuries = _injury_entries(user_profile)
    filtered = []

    for exercise in exercises:
        required_equipment = {
            str(item).strip().casefold().replace(" ", "_")
            for item in _as_items(exercise.get("equipment"))
        } - {"bodyweight"}
        if not required_equipment.issubset(user_equipment):
            continue
        if EXPERIENCE_LEVELS.get(
            str(exercise.get("difficulty") or "beginner").casefold(), 0
        ) > user_level:
            continue

        cautions = _as_items(exercise.get("injury_caution"))
        muscle_group = str(exercise.get("muscle_group") or "").casefold()
        blocked = any(
            _injury_matches(str(caution), name, context)
            or (
                severity in {"acute", "severe", "high"}
                and _severe_injury_affects_group(muscle_group, name, context)
            )
            for caution in cautions or [muscle_group]
            for name, severity, context in injuries
        )
        if blocked:
            continue
        filtered.append(exercise)
    return filtered


def _template_equipment_matches(template, equipment):
    required = {
        str(item).strip().casefold().replace(" ", "_")
        for item in _as_items(template.get("equipment"))
    } - {"bodyweight"}
    return required.issubset(equipment)


def get_recommended_template(user_profile, history):
    """Return a compatible legacy template, requiring every listed item of equipment."""
    templates = load_json("workout_templates.json")
    user_goal = str(user_profile.get("goal") or "general_fitness").casefold()
    user_exp = str(user_profile.get("experience") or "beginner").casefold()
    user_level = EXPERIENCE_LEVELS.get(user_exp, 0)
    equipment = _equipment_set(user_profile)
    recent_template_ids = set(history.get("recent_template_ids") or [])
    last_muscles = {
        item.strip().casefold()
        for item in str(history.get("last_muscle_group") or "").split(",")
        if item.strip()
    }

    available = [
        template for template in templates
        if EXPERIENCE_LEVELS.get(str(template.get("experience", "")).casefold(), 99) <= user_level
        and _template_equipment_matches(template, equipment)
        and template.get("id") not in recent_template_ids
    ]
    recovery_safe = [
        template for template in available
        if not last_muscles.intersection(
            str(group).casefold() for group in template.get("muscle_groups", [])
        )
    ]
    if recovery_safe:
        available = recovery_safe
    elif history.get("recovery_required", False):
        return None
    if not available:
        return None

    available.sort(
        key=lambda template: (
            template.get("goal") == user_goal,
            template.get("experience") == user_exp,
            -int(template.get("duration_minutes", 0)),
            template.get("id", ""),
        ),
        reverse=True,
    )
    recommendation = dict(available[0])
    recommendation["goal_match"] = recommendation.get("goal") == user_goal
    recommendation["experience_match"] = recommendation.get("experience") == user_exp
    return recommendation


def map_template_to_exercises(template_id):
    """Hydrate a legacy workout template's exercise references."""
    exercises = load_json("exercises.json")
    template = next(
        (item for item in load_json("workout_templates.json") if item["id"] == template_id),
        None,
    )
    if not template:
        return []
    exercise_ids = set(template.get("template_exercises") or [])
    return [exercise for exercise in exercises if exercise.get("id") in exercise_ids]


def _training_days(profile):
    try:
        days = int(profile.get("training_days") or 3)
    except (TypeError, ValueError):
        days = 3
    return min(max(days, 1), 6)


def _weekly_splits(training_days):
    splits = {
        1: ["full_body"],
        2: ["upper", "lower"],
        3: ["full_body", "full_body", "full_body"],
        4: ["upper", "lower", "upper", "lower"],
        5: ["upper", "lower", "push", "pull", "legs"],
        6: ["push", "pull", "legs", "push", "pull", "legs"],
    }
    return splits[training_days]


def _scheduled_days(training_days):
    schedules = {
        1: [2],
        2: [1, 4],
        3: [0, 2, 4],
        4: [0, 2, 4, 6],
        5: [0, 1, 3, 4, 6],
        6: [0, 1, 2, 4, 5, 6],
    }
    return schedules[training_days]


def _recent_group_exposure(history, today):
    exposure = {}
    for item in history:
        if item.get("status") != "completed" or not item.get("date"):
            continue
        try:
            workout_date = date.fromisoformat(str(item["date"])[:10])
        except ValueError:
            continue
        age_days = (today - workout_date).days
        if age_days < 0 or age_days > 7:
            continue
        groups = {
            group.strip().casefold()
            for group in str(item.get("muscle_group") or "").split(",")
            if group.strip()
        }
        for group in groups:
            previous = exposure.get(group)
            if previous is None or workout_date > previous[0]:
                exposure[group] = (workout_date, item.get("difficulty"))
    return exposure


def _performance_for(exercise_id, history):
    for workout in history:
        performance = workout.get("performance") or {}
        if isinstance(performance, dict) and exercise_id in performance:
            record = performance[exercise_id]
            if isinstance(record, dict):
                return record
    return {}


def _prescription(exercise, profile, history):
    goal = str(profile.get("goal") or "general_fitness").casefold()
    experience = str(profile.get("experience") or "beginner").casefold()
    base_sets = {"beginner": 2, "intermediate": 3, "advanced": 4}.get(experience, 2)
    if goal == "strength":
        rep_range, rest_seconds = "4-6", 150
    elif goal == "muscle_gain":
        rep_range, rest_seconds = "8-12", 90
    elif goal == "fat_loss":
        rep_range, rest_seconds = "10-15", 60
    else:
        rep_range, rest_seconds = "8-12", 75

    performance = _performance_for(exercise.get("id", ""), history)
    effort = str(performance.get("effort") or "").casefold()
    previous_sets = performance.get("sets")
    try:
        if previous_sets is not None:
            base_sets = min(max(int(previous_sets), 1), 5)
    except (TypeError, ValueError):
        pass
    if effort in {"hard", "very_hard", "very hard"}:
        base_sets = max(1, base_sets - 1)
    elif effort == "easy":
        base_sets = min(5, base_sets + 1)

    previous_weight = performance.get("weight_kg")
    previous_reps = performance.get("reps")
    try:
        weight = float(previous_weight) if previous_weight is not None else None
    except (TypeError, ValueError):
        weight = None
    try:
        reps = int(previous_reps) if previous_reps is not None else 0
    except (TypeError, ValueError):
        reps = 0

    progression = "Add reps gradually while keeping good form; increase resistance once every set reaches the top of the range."
    suggested_weight = weight
    if weight is not None:
        try:
            top_reps = int(rep_range.split("-")[-1])
        except ValueError:
            top_reps = 12
        if reps >= top_reps and effort in {"easy", "moderate"}:
            increment = 0.025 if goal == "strength" else 0.05
            suggested_weight = round(weight * (1 + increment), 1)
            progression = f"Previous top-end reps were comfortable; try about {suggested_weight:g} kg, otherwise keep the prior load."
        else:
            progression = "Keep the last recorded load and build reps with controlled technique before adding weight."

    return {
        "sets": base_sets,
        "reps": rep_range,
        "rest": f"{rest_seconds} sec",
        "intensity": "RPE 7-8; finish with 2-3 good reps in reserve",
        "weight_kg": suggested_weight,
        "progression": progression,
    }


def _build_session(split, profile, history, today, used_exercise_ids, user_id):
    exercises = filter_exercises_by_context(load_json("exercises.json"), profile)
    groups = MUSCLE_GROUPS[split]
    recent_exposure = _recent_group_exposure(history, today)
    available_groups = []
    for group in groups:
        exposure = recent_exposure.get(group)
        if exposure:
            last_date, effort = exposure
            age_days = (today - last_date).days
            elapsed_hours = age_days * 24
            count = 0
            for workout in history:
                if workout.get("status") != "completed" or not workout.get("date"):
                    continue
                workout_groups = {
                    value.strip().casefold()
                    for value in str(workout.get("muscle_group") or "").split(",")
                }
                try:
                    workout_age = (
                        today - date.fromisoformat(str(workout["date"])[:10])
                    ).days
                except ValueError:
                    continue
                if group in workout_groups and 0 <= workout_age <= 7:
                    count += 1
            required_hours = recovery_rules.required_recovery_hours(
                group, profile, count, effort
            )
            if elapsed_hours < required_hours:
                continue
        available_groups.append(group)

    if not available_groups:
        return []

    candidates = [
        exercise for exercise in exercises
        if str(exercise.get("muscle_group") or "").casefold() in available_groups
    ]
    candidate_order = {
        exercise["id"]: index
        for index, exercise in enumerate(
            rank_workouts(candidates, profile, history, user_id)
        )
    }
    candidates.sort(
        key=lambda exercise: (
            exercise.get("id") in used_exercise_ids,
            candidate_order[exercise["id"]],
        )
    )

    chosen = []
    group_counts = {group: 0 for group in available_groups}
    movement_counts = {}
    for exercise in candidates:
        group = str(exercise.get("muscle_group") or "").casefold()
        movement = str(exercise.get("movement") or "")
        if group_counts[group] >= 2 or movement_counts.get(movement, 0) >= 2:
            continue
        chosen.append(exercise)
        group_counts[group] += 1
        movement_counts[movement] = movement_counts.get(movement, 0) + 1
        if len(chosen) >= 6:
            break

    # If history and equipment leave too few unique options, prefer a repeat over an empty session.
    if len(chosen) < 3:
        for exercise in candidates:
            if exercise not in chosen:
                chosen.append(exercise)
            if len(chosen) >= 3:
                break

    result = []
    for exercise in chosen:
        used_exercise_ids.add(exercise.get("id"))
        result.append({
            **exercise,
            "muscle_group": exercise.get("muscle_group"),
            **_prescription(exercise, profile, history),
        })
    return result


def generate_weekly_workout_plan(profile, history, user_id=""):
    """Construct a seven-day split and dynamically prescribe each safe session."""
    today = date.today()
    training_days = _training_days(profile)
    splits = _weekly_splits(training_days)
    scheduled_days = set(_scheduled_days(training_days))
    used_exercise_ids = set()
    schedule = []

    for weekday in range(7):
        day_name = (today - timedelta(days=today.weekday() - weekday)).strftime("%A")
        if weekday not in scheduled_days:
            schedule.append({
                "day": day_name,
                "day_index": weekday,
                "is_rest_day": True,
                "title": "Rest and recovery",
                "muscle_groups": [],
                "exercises": [],
                "duration_minutes": 0,
                "id": f"rest_{weekday}",
            })
            continue

        split_index = sum(1 for day in scheduled_days if day < weekday)
        split = splits[split_index]
        session_exercises = _build_session(
            split, profile, history, today, used_exercise_ids, user_id
        )
        groups = list(dict.fromkeys(
            exercise["muscle_group"] for exercise in session_exercises
        ))
        schedule.append({
            "day": day_name,
            "day_index": weekday,
            "is_rest_day": not session_exercises,
            "title": f"{split.replace('_', ' ').title()} - {str(profile.get('goal') or 'general fitness').replace('_', ' ').title()}",
            "muscle_groups": groups,
            "exercises": session_exercises,
            "duration_minutes": 10 + len(session_exercises) * 8 if session_exercises else 0,
            "difficulty": str(profile.get("experience") or "beginner"),
            "id": "dynamic_{}_{}_{}".format(
                split,
                weekday,
                hashlib.sha256(
                    "{}|{}|{}|{}".format(
                        user_id,
                        split,
                        weekday,
                        "|".join(exercise.get("id", "") for exercise in session_exercises),
                    ).encode()
                ).hexdigest()[:8],
            ),
        })

    return schedule


def generate_workout(profile, history, user_id="", disliked_workout_ids=None):
    """Build the current session from available exercises and attach the weekly plan."""
    today = date.today().weekday()
    schedule = generate_weekly_workout_plan(profile, history, user_id)
    todays_plan = schedule[today]
    if todays_plan.get("id") in set(disliked_workout_ids or []):
        schedule = generate_weekly_workout_plan(
            profile,
            history,
            f"{user_id}:alternative:{todays_plan['id']}",
        )
        todays_plan = schedule[today]
    if todays_plan["is_rest_day"]:
        scheduled_today = today in set(_scheduled_days(_training_days(profile)))
        if scheduled_today and not filter_exercises_by_context(
            load_json("exercises.json"), profile
        ):
            return {
                "type": "workout_recommendation",
                **todays_plan,
                "recommended_for": date.today().isoformat(),
                "is_recovery_day": False,
                "reasons": [
                    "No catalog exercise satisfies your current equipment, experience, and injury restrictions."
                ],
                "safety_note": "No safe workout was generated. Update your profile or consult a qualified professional.",
                "weekly_schedule": schedule,
            }
        return {
            "type": "recovery_recommendation",
            **todays_plan,
            "recommended_for": date.today().isoformat(),
            "is_recovery_day": True,
            "safety_note": "Keep recovery comfortable and stop if you feel pain. This is not medical advice.",
            "reasons": ["Your weekly training frequency includes planned recovery to support adaptation."],
            "weekly_schedule": schedule,
        }
    return {
        "type": "workout_recommendation",
        **todays_plan,
        "recommended_for": date.today().isoformat(),
        "is_recovery_day": False,
        "goal_match": True,
        "experience_match": True,
        "reasons": [
            f"Session built for your {str(profile.get('goal') or 'general_fitness').replace('_', ' ')} goal and {str(profile.get('experience') or 'beginner')} experience.",
            "Exercise selection uses your available equipment, injury notes, and recent muscle-group training.",
            "Sets, rep ranges, rest, and progression use your goal and logged exercise performance.",
        ],
        "safety_note": "Use comfortable loads, maintain controlled form, and stop if you feel pain.",
        "weekly_schedule": schedule,
    }
