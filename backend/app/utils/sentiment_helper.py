"""
Helper function to fetch and cache sentiment data for a game
"""
from sqlalchemy.orm import Session
from .. import models
from ..steam_api import SteamAPIClient
from datetime import datetime


def fetch_and_cache_sentiment(game_id: int, steam_app_id: int, db: Session) -> bool:
    """
    Fetch sentiment data from Steam API and cache it in game_sentiment table
    
    Args:
        game_id: Database game ID
        steam_app_id: Steam App ID
        db: Database session
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Fetch from Steam API
        review_summary = SteamAPIClient.get_app_reviews(
            app_id=int(steam_app_id),
            language="all",
            num_per_page=0
        )
        
        if review_summary and review_summary.get("success") == 1:
            summary = review_summary.get("query_summary", {})
            total = summary.get("total_reviews", 0)
            positive = summary.get("total_positive", 0)
            negative = summary.get("total_negative", 0)
            review_score_desc = summary.get("review_score_desc", "No user reviews")
            
            # Calculate percentages
            if total > 0:
                pos_pct = round((positive / total * 100), 1)
                neg_pct = round((negative / total * 100), 1)
            else:
                pos_pct = 0
                neg_pct = 0
            
            # Check if sentiment already exists
            sentiment = db.query(models.GameSentiment).filter(
                models.GameSentiment.game_id == game_id
            ).first()
            
            if sentiment:
                # Update existing
                sentiment.positive_percent = pos_pct
                sentiment.negative_percent = neg_pct
                sentiment.total_reviews = total
                sentiment.review_score_desc = review_score_desc
                sentiment.last_updated = datetime.now()
            else:
                # Create new
                sentiment = models.GameSentiment(
                    game_id=game_id,
                    positive_percent=pos_pct,
                    negative_percent=neg_pct,
                    total_reviews=total,
                    review_score_desc=review_score_desc,
                    last_updated=datetime.now()
                )
                db.add(sentiment)
            
            # Update Game rating (0-10 scale based on positive percentage)
            rating_val = round(pos_pct / 10.0, 1)
            game = db.query(models.Game).filter(models.Game.id == game_id).first()
            if game:
                game.rating = rating_val
                print(f"  [OK] Updated Game {game_id} rating to {rating_val}")
            
            db.commit()
            print(f"[OK] Cached sentiment for game {game_id}: {review_score_desc} ({pos_pct}% positive)")
            return True
            
    except Exception as e:
        print(f"[ERROR] Error fetching sentiment for game {game_id}: {e}")
        return False
