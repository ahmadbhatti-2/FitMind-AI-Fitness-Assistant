-- FitMind Enterprise Database Schema & Performance Tuning

-- Core authentication and user account details
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User health profiles with JSONB fields for native list/array serialization
CREATE TABLE profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    age INTEGER,
    gender VARCHAR(20),
    height FLOAT,
    weight FLOAT,
    goal VARCHAR(50),
    experience VARCHAR(30),
    training_days INTEGER,
    equipment JSONB,     -- Equipment array for quick array operations
    diet_preference VARCHAR(50),
    allergies JSONB,     -- Allergen list for safety filtering
    restrictions JSONB,  -- Dietary restriction flags
    injuries JSONB,      -- Medical contraindications for safety guardrails
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log of workout sessions used for muscle group recovery checks
CREATE TABLE workout_history (
    history_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    template_id VARCHAR(50),
    muscle_group VARCHAR(50),
    workout_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20),
    difficulty_felt VARCHAR(20),
    performance JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log of user meals used for repetition filtering
CREATE TABLE meal_history (
    meal_log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    meal_id VARCHAR(50),
    meal_type VARCHAR(30),
    meal_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User feedback entries for item blacklisting and preference scoring
CREATE TABLE feedback (
    feedback_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    item_id VARCHAR(50),
    item_type VARCHAR(20),
    feedback_type VARCHAR(30),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Health and metric progress tracking over time
CREATE TABLE progress (
    progress_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    metric_date DATE DEFAULT CURRENT_DATE,
    weight FLOAT,
    metric_type VARCHAR(50),
    notes TEXT
);

-- Composite indexes to accelerate history queries and recency lookups
CREATE INDEX idx_workout_history_user ON workout_history(user_id, workout_date);
CREATE INDEX idx_meal_history_user ON meal_history(user_id, meal_date);
CREATE INDEX idx_feedback_user ON feedback(user_id);
CREATE INDEX idx_progress_user ON progress(user_id, metric_date);

-- Trigger function to automatically update row mutation timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Automatically touch updated_at column before row modification
CREATE TRIGGER update_profiles_modtime
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();