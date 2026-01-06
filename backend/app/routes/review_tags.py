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
async def get_review_tags(
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
            # If explicit refresh, user expects new data, but maybe fast?
            # Let's do fast then background deep
            result = service.generate_tags_for_game(game_id, top_n=10, max_reviews=300)
            if background_tasks:
                 background_tasks.add_task(service.generate_tags_for_game, game_id, top_n=10, max_reviews=1500)
        else:
            # Get from cache or generate if needed
            # Use 300 for synchronous generation (Fast First Load: ~3-5s)
            result = service.refresh_tags_if_needed(game_id, max_age_days=7, max_reviews=300)
            
            # If the result was newly generated (or even if cached but old?), we could trigger deep update.
            # But simpler: If we just generated (how do we know?), trigger deep.
            # Actually, just ALWAYS trigger deep update in background if we returned result.
            # Use a check?
            # Let's just trigger deep optimization in background to be safe/ensured.
            # This ensures eventually it becomes 1500.
            if background_tasks:
                background_tasks.add_task(service.generate_tags_for_game, game_id, top_n=10, max_reviews=1500)
        
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
