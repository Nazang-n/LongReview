"""
News API routes
Handles HTTP requests for news endpoints
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/")
async def get_news(page: Optional[str] = Query(None, description="Pagination token")):
    """
    Fetch Thai gaming news from NewsData.io API
    
    Args:
        page: Optional pagination token for next page
        
    Returns:
        Dict containing news articles and pagination info
    """
    return await NewsService.fetch_news(page)


@router.get("/featured")
async def get_featured_news():
    """
    Get the featured news (first article from latest news)
    
    Returns:
        Featured news item or None
    """
    return await NewsService.get_featured_news()


@router.post("/clear-cache")
async def clear_news_cache():
    """
    Clear the news cache (admin endpoint)
    
    Returns:
        Success message
    """
    return NewsService.clear_cache()
