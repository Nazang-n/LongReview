"""
Admin API routes
Handles administrative functions like manual updates
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict
from ..database import get_db
from ..scheduler import update_all_sentiments, update_review_tags

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/review-tags/update")
async def trigger_review_tags_update(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger review tag update for all games (admin endpoint)
    
    This will update review tags for games that:
    - Have no tags yet
    - Have tags older than 7 days
    
    Returns:
        Status message and statistics about the update
    """
    from ..scheduler import update_review_tags
    
    try:
        stats = update_review_tags()
        
        return {
            "status": "success",
            "message": f"Checked {stats['games_checked']} games: {stats['updated']} updated, {stats['skipped']} skipped",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update review tags: {str(e)}",
            "stats": {
                "games_checked": 0,
                "updated": 0,
                "skipped": 0,
                "errors": 0
            }
        }


@router.post("/sentiment/update")
async def trigger_sentiment_update(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger sentiment update for all games (admin endpoint)
    
    Returns:
        Status message and statistics about the update
    """
    from ..scheduler import update_all_sentiments
    
    try:
        stats = update_all_sentiments()
        
        return {
            "status": "success",
            "message": f"Updated {stats['updated']} games, {stats['errors']} errors",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update sentiments: {str(e)}",
            "stats": {
                "games_processed": 0,
                "updated": 0,
                "errors": 0
            }
        }


@router.post("/reviews/update")
async def trigger_thai_reviews_update(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger Thai review fetching for all games (admin endpoint)
    
    This will fetch Thai reviews from Steam for games that:
    - Have never been fetched
    - Haven't been updated in 24+ hours
    
    Reviews will be displayed in game detail pages under "รีวิวจาก Steam (ภาษาไทย)"
    
    Returns:
        Status message and statistics about the update
    """
    from ..services.review_scheduler import trigger_manual_update
    
    # Run synchronously to get stats (it's already fast enough)
    try:
        stats = trigger_manual_update()
        
        return {
            "status": "success",
            "message": f"Updated {stats['games_processed']} games: {stats['successful']} successful, {stats['failed']} failed",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update Thai reviews: {str(e)}",
            "stats": {
                "games_processed": 0,
                "successful": 0,
                "failed": 0,
                "total_new_reviews": 0
            }
        }
