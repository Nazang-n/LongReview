"""
Review Tags Routes
API endpoints for game review tags
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict
from ..database import get_db
from ..services.review_tags_service import ReviewTagsService


router = APIRouter(prefix="/api/games", tags=["review-tags"])


@router.get("/{game_id}/review-tags")
def get_review_tags(
    game_id: int,
    refresh: bool = False,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get review tags for a game
    """
    try:
        service = ReviewTagsService(db)
        

        if refresh:
            # Force regenerate tags
            # User requested 1500 reviews even if slow
            result = service.generate_tags_for_game(game_id, top_n=10, max_reviews=1500)
        else:
            # Get from cache or generate if needed
            # User requested 1500 reviews (Note: Will take ~30s if not cached)
            result = service.refresh_tags_if_needed(game_id, max_age_days=7, max_reviews=1500)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting review tags: {str(e)}"
        )


@router.post("/{game_id}/review-tags/refresh")
async def refresh_review_tags(
    game_id: int,
    top_n: int = 10,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Force refresh review tags for a game
    
    Args:
        game_id: Game ID
        top_n: Number of top tags to generate (default: 10)
        db: Database session
        
    Returns:
        Dict with newly generated tags
    """
    try:
        service = ReviewTagsService(db)
        result = service.generate_tags_for_game(game_id, top_n)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing review tags: {str(e)}"
        )
