-- Migration script to add Steam review support to review table
-- Run this script on your database to add the necessary columns

-- Note: steam_app_id column already exists in game table, so we skip adding app_id

-- Add Steam review fields to review table
ALTER TABLE review ADD COLUMN IF NOT EXISTS is_steam_review BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE review ADD COLUMN IF NOT EXISTS steam_author VARCHAR(255);
ALTER TABLE review ADD COLUMN IF NOT EXISTS voted_up BOOLEAN;
ALTER TABLE review ADD COLUMN IF NOT EXISTS helpful_count INTEGER DEFAULT 0;
ALTER TABLE review ADD COLUMN IF NOT EXISTS playtime_hours FLOAT;

-- Create index on is_steam_review for faster queries
CREATE INDEX IF NOT EXISTS idx_review_is_steam ON review(is_steam_review);
