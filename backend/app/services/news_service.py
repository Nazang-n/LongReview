"""
News service
Business logic for news-related operations
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.config.settings import settings
from app.utils.cache import cache
from app.utils.mappers import map_news_item, clean_description
from app.database import get_db
from app.models import News


class NewsService:
    """Service class for news operations"""
    
    @staticmethod
    def _is_sports_news(article: Dict[str, Any]) -> bool:
        """
        Check if an article is sports-related news or non-gaming content
        
        Args:
            article: News article data
            
        Returns:
            True if article is sports news or non-gaming content, False otherwise
        """
        # Primary sports keywords (strong indicators)
        primary_sports_keywords = [
            "กีฬา", "นักกีฬา", "ทีมชาติ", "โอลิมปิก",
            "ฟุตบอล", "บาสเกตบอล", "วอลเลย์บอล", "แบดมินตัน",
            "เทนนิส", "ว่ายน้ำ", "มวย", "มวยไทย", "กรีฑา",
            "sea games", "seagames", "อาเซียน เกมส์",
            # Football teams and leagues (including abbreviations)
            "แมนยู", "แมนฯ ยู", "แมนฯยู", "แมน ยู",
            "แมนซิตี้", "แมนฯ ซิตี้", "แมน ซิตี้",
            "ลิเวอร์พูล", "เชลซี", "อาร์เซน่อล",
            "บาร์เซโลน่า", "เรอัลมาดริด", "พรีเมียร์ลีก", "ลาลีกา",
            "ยูฟ่า", "ชปล.", "ฟีฟ่า", "กุนซือ", "ผู้จัดการทีม",
            "นัดถัดไป", "โปรแกรม 5 นัด", "เจอของหนัก", "ยุคไร้กุนซือ",
            "คาร์ริค", "ตั้งกุนซือ", "คุมทัพ", "ซีซั่น",
            # Football-specific: Player names and terms
            "แข้ง", "ปีศาจแดง", "แม็กไกวร์", "สัญญาแม็กไกวร์",
            "ต่อสัญญา", "นักเตะ", "ผู้เล่น", "ดาวซัลโว",
            "กองหลัง", "กองกลาง", "กองหน้า", "ประตู",
            "ช้างศึก", "ทีมชาติไทย", "เติร์กเมนิสถาน",
            "เปิดขายบัตร", "ขายบัตร", "บัตรเชียร์", "เชียร์ทีมชาติ",
            "นัดชิง", "เลกแรก", "เลกที่สอง", "ลงสนาม",
            # Badminton specific
            "กุลวุฒิ", "คริสตี้", "แบดมินตัน โอเพ่น", "โอเพ่น 20",
            "น้องเมย์", "เฟม", "บาส-เฟม", "อินเดีย โอเพ่น", "india open",
            "คู่เสือเหลือง", "แบดอินเดีย", "ลุยต่อรอบสอง", "ฉลุยเข้ารอบสอง",
            "ไล่ต้อนสาวญี่ปุ่น", "เฉือนคู่", "ชนะเซต", "ไล่ต้อน", "รอบสอง",
            "บางกอก โอเพ่น", "bangkok open", "แม็กซิมัส", "พัชรินทร์",
            "เข้ารอบก่อนรอง", "ไอทีเอฟเวิลด์", "itf world", "คว้าชัย",
            # Tennis specific
            "เทนนิส", "ศึกเทนนิส", "รอบก่อนรอง", "รอบรอง",
            # Basketball specific  
            "บาส", "nba", "บาสเกตบอล", "สนามบาส", "ลูกบาส",
            # Children's day and non-gaming events
            "วันเด็ก", "เพลย์แลนด์", "สวนสนุก", "พิกัดเที่ยว",
            "กิจกรรมสร้างสรรค์", "งานวันเด็ก"
        ]
        
        # Secondary sports indicators (weaker indicators, need multiple)
        secondary_sports_keywords = [
            "แข่งขัน", "การแข่งขัน", "เหรียญทอง", "เหรียญเงิน", "เหรียญทองแดง",
            "แชมป์", "แชมเปี้ยน", "ชิงแชมป์", "รอบชิงชนะเลิศ",
            "สนาม", "นัดชิง", "รอบคัดเลือก", "คัดเลือก",
            "ทะยานชิง", "ชนะมือ", "คว้าแชมป์", "ป้องกันแชมป์",
            "คู่ชิง", "ปะทะ", "ซุปตาร์", "ซูเปอร์สตาร์",
            "ย้อนวัยเด็ก", "ทะลุชิง", "โชว์ฟอร์ม"
        ]
        
        # Entertainment/Celebrity keywords (non-gaming content)
        entertainment_keywords = [
            "บิลบอร์ด", "คอนเสิร์ต", "แฟนมีต", "งานแถลงข่าว",
            "เซเลบ", "ดารา", "นักร้อง", "นักแสดง"
        ]
        
        # Political keywords (filter out political news)
        political_keywords = [
            "การเมือง", "นักการเมือง", "พรรคการเมือง", "รัฐบาล",
            "นายกรัฐมนตรี", "รัฐมนตรี", "ส.ส.", "ส.ว.", "ผู้ว่าฯ",
            "เลือกตั้ง", "โหวต", "ลงคะแนน", "ประชามติ",
            "ปชป.", "พปชร.", "เพื่อไทย", "ก้าวไกล", "ประชาธิปัตย์",
            "อภิสิทธิ์", "เศรษฐา", "พิธา", "ทักษิณ", "ยิ่งลักษณ์",
            "แดง-น้ำเงิน", "โยนกันไปมา", "กลับมาแข็งแกร่ง",
            "รัฐสภา", "สภาผู้แทนราษฎร", "วุฒิสภา", "คณะรัฐมนตรี",
            # Diplomatic and international relations
            "ทูต", "เอกอัครราชทูต", "สถานทูต", "กงสุล", "กงสุลใหญ่",
            "ความสัมพันธ์ทางการทูต", "แฟร์", "งานแฟร์", "บริติชแฟร์",
            "เยือน", "เยือนเชียงใหม่", "เยือนไทย", "ผู้แทนต่างประเทศ",
            "ความร่วมมือระหว่างประเทศ", "ความสัมพันธ์ระหว่างประเทศ"
        ]
        
        # Non-gaming content keywords
        non_gaming_keywords = [
            "board game", "card game", "tabletop", "puzzle",
            "tech gadget", "smartphone", "laptop", "tablet",
            "politics", "election", "trump", "biden",
            "plastic", "environment", "climate",
            "holiday gift", "christmas", "shopping",
            "performance review", "business", "stock market"
        ]
        
        # Positive gaming indicators
        gaming_keywords = [
            "video game", "videogame", "pc game", "console", "playstation", "xbox", "nintendo",
            "steam", "epic games", "game pass", "esports", "e-sports",
            "rpg", "fps", "mmorpg", "moba", "battle royale",
            "gameplay", "trailer", "dlc", "update", "patch",
            "เกมคอม", "เกมมือถือ", "เกมคอนโซล", "เกมออนไลน์"
        ]
        
        # Combine title and description for checking
        title = (article.get("title") or "").lower()
        description = (article.get("description") or "").lower()
        content = f"{title} {description}"
        
        # Check for primary sports keywords (any one is enough)
        if any(keyword in content for keyword in primary_sports_keywords):
            return True
        
        # Check for entertainment keywords (any one is enough)
        if any(keyword in content for keyword in entertainment_keywords):
            return True
        
        # Check for political keywords (any one is enough)
        if any(keyword in content for keyword in political_keywords):
            return True
        
        # Check for non-gaming keywords (filter out if found)
        if any(keyword in content for keyword in non_gaming_keywords):
            return True
        
        # Check for secondary keywords (need at least 2)
        secondary_count = sum(1 for keyword in secondary_sports_keywords if keyword in content)
        if secondary_count >= 2:
            return True
        
        # Don't require gaming keywords since our search query already targets gaming
        # Just filter out obvious non-gaming content above
        return False
    
    @staticmethod
    async def fetch_news(page: Optional[str] = None, min_results: int = 15) -> Dict[str, Any]:
        """
        Fetch Thai gaming news from NewsData.io API with pagination
        Fetches multiple pages if needed to get enough gaming news after filtering
        
        Args:
            page: Optional pagination token for next page
            min_results: Minimum number of gaming news articles to fetch (default: 15)
            
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
            # Fetch more pages to maximize Thai gaming news coverage
            max_pages = 4 if page else 6
            pages_fetched = 0
            next_page_token = None
            
            async with httpx.AsyncClient() as client:
                # Initial load: target 20 articles, Load more: target 15 articles
                target_results = 20 if not page else 15
                
                while len(all_filtered_articles) < target_results and pages_fetched < max_pages:
                    # Build API parameters
                    params = {
                        "apikey": settings.NEWSDATA_API_KEY,
                        "q": settings.NEWSDATA_QUERY
                    }
                    
                    # Only add country filter if specified
                    if settings.NEWSDATA_COUNTRY:
                        params["country"] = settings.NEWSDATA_COUNTRY
                    
                    # Only add language filter if specified
                    if settings.NEWSDATA_LANGUAGE:
                        params["language"] = settings.NEWSDATA_LANGUAGE
                    
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
            
            # Sort by publication date (newest first)
            all_filtered_articles.sort(
                key=lambda x: x.get("pubDate", ""), 
                reverse=True
            )
            
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
    
    # ============ Database Operations ============
    
    @staticmethod
    async def sync_news_from_api(db: Session, max_pages: int = 6) -> Dict[str, Any]:
        """
        Fetch news from NewsData.io API and save to database
        
        Args:
            db: Database session
            max_pages: Maximum pages to fetch
            
        Returns:
            Sync statistics
        """
        try:
            new_count = 0
            updated_count = 0
            current_page = None
            pages_fetched = 0
            
            async with httpx.AsyncClient() as client:
                while pages_fetched < max_pages:
                    # Build API parameters
                    params = {
                        "apikey": settings.NEWSDATA_API_KEY,
                        "q": settings.NEWSDATA_QUERY
                    }
                    
                    if settings.NEWSDATA_COUNTRY:
                        params["country"] = settings.NEWSDATA_COUNTRY
                    
                    if settings.NEWSDATA_LANGUAGE:
                        params["language"] = settings.NEWSDATA_LANGUAGE
                    
                    if current_page:
                        params["page"] = current_page
                    
                    # Call API
                    response = await client.get(
                        settings.NEWSDATA_API_URL,
                        params=params,
                        timeout=10.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Process articles
                    articles = data.get("results", [])
                    for article in articles:
                        # Filter out sports/non-gaming
                        if NewsService._is_sports_news(article):
                            continue
                        
                        # Save to database
                        result = NewsService.save_article_to_db(db, article)
                        if result == "new":
                            new_count += 1
                        elif result == "updated":
                            updated_count += 1
                    
                    # Get next page
                    current_page = data.get("nextPage")
                    pages_fetched += 1
                    
                    if not current_page:
                        break
            
            return {
                "status": "success",
                "new_articles": new_count,
                "updated_articles": updated_count,
                "pages_fetched": pages_fetched
            }
            
        except httpx.HTTPStatusError as e:
            import traceback
            print(f"HTTP Status Error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            if e.response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="API rate limit reached. Please try again later."
                )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync news: {str(e)}"
            )
        except Exception as e:
            import traceback
            print(f"General Error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync news: {str(e)}"
            )

    
    @staticmethod
    def save_article_to_db(db: Session, article: Dict[str, Any]) -> str:
        """
        Save or update a single article in database
        
        Args:
            db: Database session
            article: Article data from API
            
        Returns:
            "new" if created, "updated" if existing article updated
        """
        article_id = article.get("article_id")
        
        # Check if article exists
        existing = db.query(News).filter(News.article_id == article_id).first()
        
        # Parse publication date
        pub_date_str = article.get("pubDate", "")
        try:
            pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
        except:
            pub_date = datetime.utcnow()
        
        if existing:
            # Update last_seen_at
            existing.last_seen_at = datetime.utcnow()
            existing.is_active = True
            db.commit()
            return "updated"
        else:
            # Create new article
            news_item = News(
                article_id=article_id,
                title=article.get("title", ""),
                description=clean_description(article.get("description", "")),
                image_url=article.get("image_url"),
                link=article.get("link", ""),
                pub_date=pub_date,
                source_name=article.get("source_name")
            )
            db.add(news_item)
            db.commit()
            return "new"
    
    @staticmethod
    def get_news_from_db(db: Session, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get news from database (newest first)
        
        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of news articles
        """
        news_items = db.query(News).filter(
            News.is_active == True
        ).order_by(
            News.pub_date.desc()
        ).offset(skip).limit(limit).all()
        
        # Convert to dict format
        results = []
        for item in news_items:
            results.append({
                "id": item.article_id,
                "title": item.title,
                "description": clean_description(item.description) if item.description else "ไม่มีคำอธิบาย",
                "image": item.image_url or "https://via.placeholder.com/800x400?text=No+Image",
                "link": item.link,
                "date": item.pub_date.strftime("%d %B %Y") if item.pub_date else "",
                "author": item.source_name
            })
        
        return results
    
    @staticmethod
    def cleanup_deleted_news(db: Session, days: int = 7) -> int:
        """
        Mark articles as inactive if not seen in API for specified days
        
        Args:
            db: Database session
            days: Number of days threshold
            
        Returns:
            Number of articles marked inactive
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = db.query(News).filter(
            and_(
                News.last_seen_at < cutoff_date,
                News.is_active == True
            )
        ).update({"is_active": False})
        
        db.commit()
        return result
    
    @staticmethod
    def get_total_active_news(db: Session) -> int:
        """Get count of active news articles"""
        return db.query(News).filter(News.is_active == True).count()
