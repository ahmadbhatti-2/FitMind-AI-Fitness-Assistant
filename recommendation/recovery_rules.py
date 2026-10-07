from datetime import date, datetime, time
import random


def required_recovery_hours(muscle_group, profile=None, recent_sessions=1, difficulty=None):
    """Estimate recovery time from muscle size, recent workload, effort, and age."""
    profile = profile or {}
    groups = {
        item.strip().casefold()
        for item in str(muscle_group or "").replace("_", " ").split(",")
        if item.strip()
    }
    large_groups = {"chest", "back", "legs", "glutes"}
    hours = 36 if groups.intersection(large_groups) else 24
    effort = str(difficulty or "").casefold()
    if effort in {"hard", "very_hard", "very hard", "maximal"}:
        hours += 18
    elif effort in {"moderate", "challenging"}:
        hours += 6
    hours += min(max(int(recent_sessions or 1) - 1, 0) * 6, 18)
    try:
        if int(profile.get("age") or 0) >= 60:
            hours += 12
    except (TypeError, ValueError):
        pass
    return hours


def calculate_recovery_window(
    last_workout_date,
    muscle_group,
    profile=None,
    recent_sessions=1,
    difficulty=None,
):
    """Estimate readiness from the specific muscle group and training stress."""
    if not last_workout_date:
        return True, "No previous record found. Ready to train!"
    try:
        if isinstance(last_workout_date, datetime):
            last_date = last_workout_date
        elif isinstance(last_workout_date, date):
            last_date = datetime.combine(last_workout_date, time.min)
        else:
            last_date = datetime.combine(
                date.fromisoformat(str(last_workout_date)[:10]), time.min
            )
    except (TypeError, ValueError):
        return False, "The last workout date is invalid; verify your training history before repeating this muscle group."

    now = datetime.now()
    hours_passed = (now - last_date).total_seconds() / 3600
    required_hours = required_recovery_hours(
        muscle_group, profile, recent_sessions, difficulty
    )
    if hours_passed < required_hours:
        remaining = max(0, round(required_hours - hours_passed))
        return False, (
            f"{muscle_group or 'This muscle group'} may need more recovery after "
            f"recent training stress; reassess in about {remaining} hours."
        )
    return True, "Recovery interval for the recent workload has elapsed."


def suggest_recovery_activity():
    """Select a low-intensity active recovery option."""
    activities = [
        "Light walking (20-30 minutes)",
        "Gentle mobility in a pain-free range",
        "Easy restorative yoga",
        "Rest and adequate sleep",
    ]
    return random.choice(activities)


def is_rest_day_required(workout_streak, recent_intensity=None):
    """Recommend recovery based on a run of sessions, with a lower threshold after hard work."""
    threshold = 5 if str(recent_intensity or "").casefold() not in {"hard", "very hard"} else 4
    if workout_streak >= threshold:
        return True, (
            f"You have trained for {workout_streak} consecutive days. "
            "A recovery day is recommended based on your recent training load."
        )
    return False, "Your recent schedule includes enough recovery. Keep listening to how you feel."
