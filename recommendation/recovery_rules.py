from datetime import datetime
import random

def calculate_recovery_window(last_workout_date, muscle_group):
    """
    Evaluates whether a target muscle group has completed the standard recovery threshold.
    """
    if not last_workout_date:
        return True, "No previous record found. Ready to train!"

    last_date = datetime.strptime(last_workout_date, '%Y-%m-%d')
    current_date = datetime.now()
    
    # Convert timedelta duration into elapsed hours to compare against recovery window
    diff = current_date - last_date
    hours_passed = diff.total_seconds() / 3600

    # Enforce standard 48-hour hypertrophy recovery window to prevent central nervous system fatigue
    if hours_passed < 48:
        remaining = 48 - hours_passed
        return False, f"Muscle group {muscle_group} needs more recovery. Approx {int(remaining)} hours left."
    
    return True, "Muscle group is fully recovered."

def suggest_recovery_activity():
    """
    Selects a low-intensity active recovery regimen for deload or rest days.
    """
    # Active recovery options designed to promote blood flow without triggering additional muscular micro-tears
    activities = [
        "Light Walking (30 mins)",
        "Full Body Stretching",
        "Yoga for Flexibility",
        "Foam Rolling"
    ]
    
    return random.choice(activities)

def is_rest_day_required(workout_streak):
    """
    Determines mandatory rest day triggers based on accumulated consecutive training sessions.
    """
    # Mandatory rest threshold: 5 consecutive days triggers a required rest day to mitigate overtraining risks
    if workout_streak >= 5:
        return True, "You've trained for 5 consecutive days. A rest day is highly recommended for optimal growth."
    
    return False, "You are on track. Keep going!"