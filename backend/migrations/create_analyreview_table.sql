-- Create analyreview table for sentiment analysis
CREATE TABLE IF NOT EXISTS analyreview (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL,
    voted_up BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_analyreview_game ON analyreview(game_id);
CREATE INDEX IF NOT EXISTS idx_analyreview_voted ON analyreview(game_id, voted_up);

-- Add comment
COMMENT ON TABLE analyreview IS 'Stores voted_up from Steam reviews for sentiment analysis. voted_up=true is positive, voted_up=false is negative';
