"""
Centralized review fetching service
Handles fetching, storing, and updating Steam reviews for games
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import requests
from sqlalchemy.orm import Session
from ..models import Game
from .. import models
from ..utils.sentiment_analyzer import SentimentAnalyzer

class ReviewService:
    """Service for managing game reviews"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def fetch_and_store_reviews(
        self, 
        db: Session, 
        game_id: int, 
        steam_app_id: int,
        max_reviews: int = None  # None = fetch all reviews
    ) -> Dict:
        """
        Fetch reviews from Steam and store in database
        
        Args:
            db: Database session
            game_id: Internal game ID
            steam_app_id: Steam App ID
            max_reviews: Maximum number of reviews to fetch (None = all reviews)
            
        Returns:
            Dictionary with statistics about fetched reviews
        """
        print(f"Fetching reviews for game {game_id} (Steam App ID: {steam_app_id})...")
        
        try:
            total_fetched = 0
            new_count = 0
            positive_count = 0
            negative_count = 0
            cursor = "*"  # Start cursor for pagination
            
            # Fetch all reviews using pagination
            while True:
                # Fetch reviews from Steam API
                url = f"https://store.steampowered.com/appreviews/{steam_app_id}"
                params = {
                    "json": 1,
                    "language": "english",
                    "filter": "all",  # Get all reviews, not just recent
                    "num_per_page": 100,  # Max per page
                    "purchase_type": "all",
                    "cursor": cursor
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if not data.get("success"):
                    print(f"  [ERROR] Steam API returned success=false")
                    break
                
                reviews = data.get("reviews", [])
                if not reviews:
                    print(f"  [INFO] No more reviews found")
                    break
                
                # Store reviews in database
                for review_data in reviews:
                    # Get vote (positive/negative)
                    voted_up = review_data.get("voted_up", False)
                    
                    new_count += 1
                    
                    if voted_up:
                        positive_count += 1
                    else:
                        negative_count += 1
                
                total_fetched += len(reviews)
                
                # Check if we should continue pagination
                cursor = data.get("cursor")
                if not cursor or cursor == "*":
                    break  # No more pages
                
                # Check max_reviews limit if specified
                if max_reviews and total_fetched >= max_reviews:
                    print(f"  [INFO] Reached max_reviews limit ({max_reviews})")
                    break
                
                # Commit every 100 reviews to avoid memory issues
                if new_count % 100 == 0 and new_count > 0:
                    db.commit()
                    print(f"  ... {new_count} reviews stored so far")
            
            # Update game's last_review_fetch timestamp
            game = db.query(Game).filter(Game.id == game_id).first()
            if game:
                game.last_review_fetch = datetime.now()
            db.commit()
            
            print(f"  [OK] Stored {new_count} new reviews ({positive_count} positive, {negative_count} negative)")
            print(f"  Total fetched: {total_fetched} reviews")
            print(f"  [OK] Updated last_review_fetch timestamp")
            
            return {
                "success": True,
                "new_reviews": new_count,
                "positive": positive_count,
                "negative": negative_count,
                "total_fetched": len(reviews)
            }
            
        except requests.RequestException as e:
            print(f"  [ERROR] Error fetching reviews: {e}")
            return {"success": False, "new_reviews": 0, "error": str(e)}
        except Exception as e:
            print(f"  [ERROR] Unexpected error: {e}")
            db.rollback()
            return {"success": False, "new_reviews": 0, "error": str(e)}
    
    def should_fetch_reviews(self, game: Game) -> bool:
        """
        Check if reviews should be fetched for a game
        
        Args:
            game: Game model instance
            
        Returns:
            True if reviews should be fetched, False otherwise
        """
        # Never fetched before
        if not game.last_review_fetch:
            return True
        
        # Fetch if last fetch was more than 24 hours ago
        time_since_fetch = datetime.now() - game.last_review_fetch
        return time_since_fetch > timedelta(hours=24)
    
    def get_games_needing_review_update(self, db: Session, limit: int = 50) -> List[Game]:
        """
        Get games that need review updates
        
        Prioritizes games that have never been fetched, then games not fetched in 1+ hour
        
        Args:
            db: Database session
            limit: Maximum number of games to return
            
        Returns:
            List of Game instances ordered by priority
        """
        # Reduced to 1 hour so hourly scheduler can continuously update games
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        # Prioritize: 1) Never fetched, 2) Not fetched in 1+ hour
        games = db.query(Game).filter(
            (Game.last_review_fetch == None) | (Game.last_review_fetch < cutoff_time),
            Game.steam_app_id != None
        ).order_by(
            Game.last_review_fetch.asc().nullsfirst()  # NULL first (never fetched), then oldest
        ).limit(limit).all()
        
        return games


# Global instance
review_service = ReviewService()
