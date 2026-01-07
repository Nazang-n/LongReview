-- Create game_sentiment table for caching Steam review sentiment
CREATE TABLE game_sentiment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    game_id INT NOT NULL UNIQUE,
    positive_percent FLOAT NULL,
    negative_percent FLOAT NULL,
    total_reviews INT NULL,
    review_score_desc VARCHAR(50) NULL,
    last_updated TIMESTAMP NULL,
    FOREIGN KEY (game_id) REFERENCES game(id) ON DELETE CASCADE,
    INDEX idx_game_sentiment_game_id (game_id),
    INDEX idx_game_sentiment_last_updated (last_updated)
);
