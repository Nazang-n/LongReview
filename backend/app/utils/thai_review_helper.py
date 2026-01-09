"""
Helper function to fetch and cache Thai reviews for a game
"""
from sqlalchemy.orm import Session
from .. import models
from ..steam_api import SteamAPIClient
from datetime import datetime


def is_thai_review(text: str, min_thai_ratio: float = 0.1) -> bool:
    """Check if review text contains Thai language."""
    if not text:
        return False
    
    # Count Thai characters (Unicode range 0E00-0E7F)
    thai_chars = sum(1 for c in text if '\u0E00' <= c <= '\u0E7F')
    # Count total alphabetic characters
    total_chars = len([c for c in text if c.isalpha()])
    
    if total_chars == 0:
        return False
    
    return (thai_chars / total_chars) >= min_thai_ratio


def fetch_and_cache_thai_reviews(game_id: int, steam_app_id: int, db: Session, max_reviews: int = 50) -> bool:
    """
    Fetch Thai reviews from Steam API and cache them in review table
    
    Args:
        game_id: Database game ID
        steam_app_id: Steam App ID
        db: Database session
        max_reviews: Maximum number of reviews to fetch (default: 50)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"  [Thai Reviews] Fetching Thai reviews for game {game_id} (steam_app_id: {steam_app_id})...")
        
        # Check if we already have Thai reviews for this game
        existing_reviews_count = db.query(models.Review).filter(
            models.Review.game_id == game_id,
            models.Review.is_steam_review == True
        ).count()
        
        if existing_reviews_count > 0:
            print(f"  [Thai Reviews] ✓ Game already has {existing_reviews_count} Steam reviews, skipping fetch")
            return True
        
        # Fetch Thai reviews from Steam API
        steam_reviews = SteamAPIClient.get_all_reviews(
            app_id=int(steam_app_id),
            language="thai",
            max_reviews=max_reviews
        )
        
        if not steam_reviews:
            print(f"  [Thai Reviews] ℹ No Thai reviews found on Steam")
            return True  # Not an error, just no content
        
        # Filter and save Thai reviews
        saved_count = 0
        processed_steam_ids = set()
        
        # Get existing steam_ids to avoid duplicates
        existing_steam_ids = {
            r[0] for r in db.query(models.Review.steam_id).filter(
                models.Review.game_id == game_id,
                models.Review.steam_id.isnot(None)
            ).all()
        }
        
        for steam_review in steam_reviews:
            rec_id = steam_review.get("recommendationid")
            review_content = steam_review.get("review", "")
            
            if not rec_id:
                continue
            
            rec_id_str = str(rec_id)
            
            # Skip duplicates
            if rec_id_str in existing_steam_ids or rec_id_str in processed_steam_ids:
                continue
            
            # Filter non-Thai reviews
            if not is_thai_review(review_content):
                continue
            
            processed_steam_ids.add(rec_id_str)
            
            # Extract review data
            playtime_minutes = steam_review.get("author", {}).get("playtime_at_review", 0)
            playtime_hours = round(playtime_minutes / 60, 1) if playtime_minutes else 0
            
            timestamp = steam_review.get("timestamp_created")
            created_date = datetime.fromtimestamp(timestamp) if timestamp else None
            
            # Create new review
            new_review = models.Review(
                game_id=game_id,
                admin_id=None,
                owner=steam_review.get("author", {}).get("steamid", "Unknown"),
                content=review_content,
                steam_id=rec_id_str,
                is_steam_review=True,
                steam_author=steam_review.get("author", {}).get("steamid", "Unknown"),
                voted_up=steam_review.get("voted_up", True),
                helpful_count=steam_review.get("votes_up", 0),
                playtime_hours=playtime_hours,
                created_at=created_date
            )
            
            db.add(new_review)
            saved_count += 1
        
        if saved_count > 0:
            db.commit()
            print(f"  [Thai Reviews] ✓ Saved {saved_count} Thai reviews for game {game_id}")
        else:
            print(f"  [Thai Reviews] ℹ No Thai reviews passed the filter")
        
        return True
        
    except Exception as e:
        print(f"  [Thai Reviews] ✗ Error fetching Thai reviews for game {game_id}: {e}")
        db.rollback()
        return False
