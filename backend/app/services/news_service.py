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
    def _is_sports_news(article: Dict[str, Any]) -> bool:
        """
        Check if an article is sports-related news
        
        Args:
            article: News article data
            
        Returns:
            True if article is sports news, False otherwise
        """
        # Primary sports keywords (strong indicators)
        primary_sports_keywords = [
            "กีฬา", "นักกีฬา", "ทีมชาติ", "โอลิมปิก",
            "ฟุตบอล", "บาสเกตบอล", "วอลเลย์บอล", "แบดมินตัน",
            "เทนนิส", "ว่ายน้ำ", "มวย", "มวยไทย", "กรีฑา",
            "sea games", "seagames", "อาเซียน เกมส์"
        ]
        
        # Secondary sports indicators (weaker indicators, need multiple)
        secondary_sports_keywords = [
            "แข่งขัน", "การแข่งขัน", "เหรียญทอง", "เหรียญเงิน", "เหรียญทองแดง",
            "แชมป์", "แชมเปี้ยน", "ชิงแชมป์", "รอบชิงชนะเลิศ",
            "สนาม", "นัดชิง", "รอบคัดเลือก", "คัดเลือก",
            "ทะยานชิง", "ชนะมือ", "คว้าแชมป์", "ป้องกันแชมป์"
        ]
        
        # Combine title and description for checking
        title = (article.get("title") or "").lower()
        description = (article.get("description") or "").lower()
        content = f"{title} {description}"
        
        # Check for primary sports keywords (any one is enough)
        if any(keyword in content for keyword in primary_sports_keywords):
            return True
        
        # Check for secondary keywords (need at least 2)
        secondary_count = sum(1 for keyword in secondary_sports_keywords if keyword in content)
        if secondary_count >= 2:
            return True
        
        return False
    
    @staticmethod
    async def fetch_news(page: Optional[str] = None, min_results: int = 10) -> Dict[str, Any]:
        """
        Fetch Thai gaming news from NewsData.io API with pagination
        Fetches multiple pages if needed to get enough gaming news after filtering
        
        Args:
            page: Optional pagination token for next page
            min_results: Minimum number of gaming news articles to fetch (default: 10)
            
        Returns:
            Dict containing news articles and pagination info
            
        Raises:
            HTTPException: If API call fails
        """
        try:
            # Check cache first (only for first page)
            if not page:
                cache_key = "news_gaming_filtered"
                cached_data = cache.get(cache_key)
                if cached_data:
                    return cached_data
            
            # Accumulate filtered articles across multiple pages
            all_filtered_articles = []
            current_page = page
            max_pages = 5  # Limit to prevent excessive API calls
            pages_fetched = 0
            next_page_token = None
            
            async with httpx.AsyncClient() as client:
                while len(all_filtered_articles) < min_results and pages_fetched < max_pages:
                    # Build API parameters
                    params = {
                        "apikey": settings.NEWSDATA_API_KEY,
                        "country": settings.NEWSDATA_COUNTRY,
                        "language": settings.NEWSDATA_LANGUAGE,
                        "q": settings.NEWSDATA_QUERY
                    }
                    
                    if current_page:
                        params["page"] = current_page
                    
                    # Call NewsData.io API
                    response = await client.get(
                        settings.NEWSDATA_API_URL,
                        params=params,
                        timeout=10.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Filter out sports news
                    articles = data.get("results", [])
                    filtered_articles = [
                        article for article in articles 
                        if not NewsService._is_sports_news(article)
                    ]
                    
                    # Add to accumulated results
                    all_filtered_articles.extend(filtered_articles)
                    
                    # Get next page token
                    next_page_token = data.get("nextPage")
                    pages_fetched += 1
                    
                    # Break if no more pages
                    if not next_page_token:
                        break
                    
                    # Set current page for next iteration
                    current_page = next_page_token
            
            # Map to internal format
            result = {
                "status": "success",
                "news": [map_news_item(article) for article in all_filtered_articles],
                "nextPage": next_page_token,
                "totalResults": len(all_filtered_articles),
                "pagesFetched": pages_fetched
            }
            
            # Cache the result (only for first page)
            if not page:
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
