-- Migration: Create news table
-- Run this SQL script in your PostgreSQL database

CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    image_url VARCHAR(1000),
    link VARCHAR(1000) NOT NULL,
    pub_date TIMESTAMP WITH TIME ZONE NOT NULL,
    source_name VARCHAR(255),
    category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_news_article_id ON news(article_id);
CREATE INDEX IF NOT EXISTS idx_news_pub_date ON news(pub_date DESC);
CREATE INDEX IF NOT EXISTS idx_news_is_active ON news(is_active);
CREATE INDEX IF NOT EXISTS idx_news_last_seen_at ON news(last_seen_at);

-- Add comment
COMMENT ON TABLE news IS 'Stores gaming news articles from NewsData.io API';
