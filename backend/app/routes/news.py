"""
News API routes
Handles HTTP requests for news endpoints
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.services.news_service import NewsService
from app.database import get_db

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/")
async def get_news(
    skip: int = Query(0, description="Number of articles to skip"),
    limit: int = Query(20, description="Number of articles to return"),
    db: Session = Depends(get_db)
):
    """
    Get Thai gaming news from database (newest first)
    
    Args:
        skip: Number of articles to skip (for pagination)
        limit: Number of articles to return
        db: Database session
        
    Returns:
        Dict containing news articles
    """
    # Get news from database
    news_list = NewsService.get_news_from_db(db, skip=skip, limit=limit)
    total = NewsService.get_total_active_news(db)
    
    # Check if database is empty, trigger sync
    if total == 0:
        sync_result = await NewsService.sync_news_from_api(db, max_pages=6)
        news_list = NewsService.get_news_from_db(db, skip=skip, limit=limit)
        total = NewsService.get_total_active_news(db)
    
    return {
        "status": "success",
        "news": news_list,
        "totalResults": total,
        "skip": skip,
        "limit": limit,
        "hasMore": (skip + limit) < total
    }


@router.get("/featured")
async def get_featured_news(db: Session = Depends(get_db)):
    """
    Get the featured news (first article from latest news)
    
    Returns:
        Featured news item or None
    """
    news_list = NewsService.get_news_from_db(db, skip=0, limit=1)
    return news_list[0] if news_list else None


@router.post("/sync")
async def sync_news(db: Session = Depends(get_db)):
    """
    Manually trigger news sync from API (admin endpoint)
    
    Returns:
        Sync statistics
    """
    result = await NewsService.sync_news_from_api(db, max_pages=6)
    return result


@router.post("/cleanup")
async def cleanup_news(
    days: int = Query(7, description="Remove articles not seen for this many days"),
    db: Session = Depends(get_db)
):
    """
    Clean up old/deleted news articles (admin endpoint)
    
    Returns:
        Number of articles cleaned up
    """
    count = NewsService.cleanup_deleted_news(db, days=days)
    return {
        "status": "success",
        "articles_cleaned": count
    }


@router.post("/clear-cache")
async def clear_news_cache():
    """
    Clear the news cache (admin endpoint)
    
    Returns:
        Success message
    """
    return NewsService.clear_cache()

