ALTER TABLE workout_history
    ADD COLUMN IF NOT EXISTS performance JSONB;
