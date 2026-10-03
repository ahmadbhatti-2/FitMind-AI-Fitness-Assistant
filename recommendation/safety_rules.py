import json
from pathlib import Path

def load_json(filename):
    file_path = Path(__file__).resolve().parent.parent / 'data' / filename
    with open(file_path, 'r') as f:
        return json.load(f)

def check_exercise_safety(exercise_id, user_injuries):
    """
    Checks if a specific exercise is safe given the user's injuries.
    """
    exercises = load_json('exercises.json')
    exercise = next((ex for ex in exercises if ex['id'] == exercise_id), None)
    
    if not exercise:
        return True, "" # Assume safe if exercise not found, or handle as error

    # Check if any of the exercise's injury cautions match the user's injuries
    for caution in exercise['injury_caution']:
        if caution in user_injuries:
            return False, f"Caution: This exercise may aggravate your {caution} injury."
    
    return True, "Safe to perform."

def filter_unsafe_exercises(exercise_list, user_injuries):
    """
    Removes all unsafe exercises from a given list based on user injuries.
    """
    safe_exercises = []
    for ex in exercise_list:
        # We check the 'injury_caution' field of each exercise
        if not any(caution in user_injuries for caution in ex.get('injury_caution', [])):
            safe_exercises.append(ex)
            
    return safe_exercises

def get_medical_disclaimer():
    """
    Returns a standard medical disclaimer for the agent to use.
    """
    return (
        "Disclaimer: I am an AI assistant, not a doctor. Please consult "
        "a healthcare professional before starting any new exercise or diet "
        "regimen, especially if you have pre-existing injuries or medical conditions."
    )
