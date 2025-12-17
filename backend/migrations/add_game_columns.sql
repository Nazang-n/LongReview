-- Add missing columns to 'game' table for Steam API data
-- Run this SQL script on your PostgreSQL database

-- Add genre column
ALTER TABLE game ADD COLUMN IF NOT EXISTS genre VARCHAR(100);

-- Add developer column
ALTER TABLE game ADD COLUMN IF NOT EXISTS developer VARCHAR(255);

-- Add publisher column
ALTER TABLE game ADD COLUMN IF NOT EXISTS publisher VARCHAR(255);

-- Add rating column
ALTER TABLE game ADD COLUMN IF NOT EXISTS rating FLOAT;

-- Optional: Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_game_genre ON game(genre);
CREATE INDEX IF NOT EXISTS idx_game_platform ON game(platform);

-- Verify columns were added
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'game' 
ORDER BY ordinal_position;
