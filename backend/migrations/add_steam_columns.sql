-- Add missing columns to games table for Steam API data
-- Run this SQL script on your database

ALTER TABLE games ADD COLUMN IF NOT EXISTS genre VARCHAR(100);
ALTER TABLE games ADD COLUMN IF NOT EXISTS developer VARCHAR(255);
ALTER TABLE games ADD COLUMN IF NOT EXISTS publisher VARCHAR(255);
ALTER TABLE games ADD COLUMN IF NOT EXISTS rating FLOAT;

-- Optional: Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_games_genre ON games(genre);
CREATE INDEX IF NOT EXISTS idx_games_platform ON games(platform);
