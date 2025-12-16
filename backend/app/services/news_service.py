"""
News service
Business logic for news-related operations
"""
from typing import Optional, Dict, Any
import httpx
from fastapi import HTTPException

from app.config.settings import settings
from app.utils.cache import cache
from app.utils.mappers import map_news_item


class NewsService:
    """Service class for news operations"""
    
    @staticmethod
    async def fetch_news(page: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch Thai gaming news from NewsData.io API
        
        Args:
            page: Optional pagination token for next page
            
        Returns:
            Dict containing news articles and pagination info
            
        Raises:
            HTTPException: If API call fails
        """
        try:
            # Check cache first
            cache_key = f"news_page_{page or 'first'}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # Build API parameters
            params = {
                "apikey": settings.NEWSDATA_API_KEY,
                "country": settings.NEWSDATA_COUNTRY,
                "q": settings.NEWSDATA_QUERY
            }
            
            if page:
                params["page"] = page
            
            # Call NewsData.io API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    settings.NEWSDATA_API_URL,
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
            
            # Map response to internal format
            result = {
                "status": "success",
                "news": [map_news_item(article) for article in data.get("results", [])],
                "nextPage": data.get("nextPage"),
                "totalResults": data.get("totalResults", 0)
            }
            
            # Cache the result
            cache.set(cache_key, result, ttl=settings.CACHE_TTL)
            
            return result
            
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch news from external API: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while fetching news: {str(e)}"
            )
    
    @staticmethod
    async def get_featured_news() -> Optional[Dict[str, Any]]:
        """
        Get the featured news (first article from latest news)
        
        Returns:
            Featured news item or None
            
        Raises:
            HTTPException: If API call fails
        """
        try:
            news_data = await NewsService.fetch_news()
            if news_data["news"]:
                return news_data["news"][0]
            return None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch featured news: {str(e)}"
            )
    
    @staticmethod
    def clear_cache() -> Dict[str, str]:
        """
        Clear the news cache
        
        Returns:
            Success message
        """
        cache.clear()
        return {"message": "News cache cleared successfully"}
