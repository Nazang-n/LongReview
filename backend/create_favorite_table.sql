-- Create favorite table for PostgreSQL
CREATE TABLE IF NOT EXISTS favorite (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, game_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_favorite_user_id ON favorite(user_id);
CREATE INDEX IF NOT EXISTS idx_favorite_game_id ON favorite(game_id);
