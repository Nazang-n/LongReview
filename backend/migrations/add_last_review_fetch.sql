-- Migration: Add last_review_fetch column to game table (PostgreSQL)
-- This tracks when reviews were last fetched for each game

-- Add the column
ALTER TABLE game 
ADD COLUMN last_review_fetch TIMESTAMP NULL;

-- Verify the column was added
\d game;
