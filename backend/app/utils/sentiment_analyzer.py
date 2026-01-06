"""
Simple sentiment analyzer for game reviews
Uses TextBlob for sentiment analysis
"""
from textblob import TextBlob

class SentimentAnalyzer:
    """Analyzes sentiment of review text"""
    
    def analyze(self, text: str) -> dict:
        """
        Analyze sentiment of text
        
        Args:
            text: Review text to analyze
            
        Returns:
            Dictionary with sentiment and score
            - sentiment: 'positive', 'negative', or 'neutral'
            - score: Float between -1 (negative) and 1 (positive)
        """
        if not text or not text.strip():
            return {"sentiment": "neutral", "score": 0.0}
        
        try:
            # Use TextBlob for sentiment analysis
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            # Classify sentiment based on polarity
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                "sentiment": sentiment,
                "score": polarity
            }
        except Exception as e:
            # Fallback to neutral if analysis fails
            print(f"Sentiment analysis error: {e}")
            return {"sentiment": "neutral", "score": 0.0}
