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
        Status message indicating the job has been queued
    """
    # Run in background to avoid blocking
    background_tasks.add_task(update_review_tags)
    
    return {
        "status": "success",
        "message": "Review tag update job has been queued and will run in the background"
    }


@router.post("/sentiment/update")
async def trigger_sentiment_update(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger sentiment update for all games (admin endpoint)
    
    Returns:
        Status message indicating the job has been queued
    """
    # Run in background to avoid blocking
    background_tasks.add_task(update_all_sentiments)
    
    return {
        "status": "success",
        "message": "Sentiment update job has been queued and will run in the background"
    }
