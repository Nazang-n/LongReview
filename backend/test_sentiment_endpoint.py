from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/reviews",
    tags=["reviews"]
)

# ... existing review endpoints ...

@router.get("/sentiment/{game_id}")
def get_steam_sentiment(game_id: int, db: Session = Depends(get_db)):
    """
    Get sentiment analysis from Steam reviews.
    Fetches ALL Steam reviews and stores only voted_up in analyreview table.
    """
    from ..steam_api import SteamAPIClient
    from sqlalchemy import text
    
    try:
        # Get steam_app_id
        result = db.execute(
            text("SELECT steam_app_id FROM game WHERE id = :game_id"),
            {"game_id": game_id}
        )
        game_row = result.fetchone()
        
        if not game_row or not game_row[0]:
            raise HTTPException(status_code=404, detail="Game not found")
        
        steam_app_id = int(game_row[0])
        
        # Check cache
        cached_count = db.query(models.AnalyReview).filter(
            models.AnalyReview.game_id == game_id
        ).count()
        
        print(f"[Sentiment] Cached: {cached_count} records for game {game_id}")
        
        # Fetch if not cached
        if cached_count == 0:
            print(f"[Sentiment] Fetching ALL reviews for app {steam_app_id}...")
            all_reviews = SteamAPIClient.get_all_reviews(
                app_id=steam_app_id,
                language="all",
                max_reviews=None
            )
            
            if not all_reviews:
                return {"success": True, "total_reviews": 0, "positive_percent": 0, "negative_percent": 0}
            
            print(f"[Sentiment] Saving {len(all_reviews)} records...")
            saved = 0
            for review in all_reviews:
                try:
                    db.add(models.AnalyReview(
                        game_id=game_id,
                        voted_up=review.get("voted_up", True)
                    ))
                    saved += 1
                    if saved % 500 == 0:
                        db.commit()
                        print(f"[Sentiment] Saved {saved}/{len(all_reviews)}...")
                except:
                    continue
            db.commit()
            print(f"[Sentiment] Saved {saved} total")
        
        # Calculate
        result = db.execute(
            text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN voted_up = TRUE THEN 1 ELSE 0 END) as positive
                FROM analyreview WHERE game_id = :game_id
            """),
            {"game_id": game_id}
        ).fetchone()
        
        total = result[0] if result else 0
        positive = result[1] if result else 0
        negative = total - positive
        
        pos_pct = round((positive / total * 100), 1) if total > 0 else 0
        neg_pct = round((negative / total * 100), 1) if total > 0 else 0
        
        print(f"[Sentiment] {total} reviews: {pos_pct}% positive, {neg_pct}% negative")
        
        return {
            "success": True,
            "total_reviews": total,
            "positive_count": positive,
            "negative_count": negative,
            "positive_percent": pos_pct,
            "negative_percent": neg_pct,
            "cached": cached_count > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[Sentiment] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
