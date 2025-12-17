"""
News Synchronization Service
Handles background tasks for syncing news from API
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.news_service import NewsService

# Configure logging
logger = logging.getLogger(__name__)

class NewsSyncService:
    """Service to handle background news synchronization"""
    
    _scheduler = None
    
    @classmethod
    def start_scheduler(cls):
        """Start the background scheduler"""
        if cls._scheduler and cls._scheduler.running:
            return
            
        cls._scheduler = AsyncIOScheduler()
        
        # Add sync job - run every 10 minutes
        cls._scheduler.add_job(
            cls.sync_job,
            IntervalTrigger(minutes=10),
            id='sync_news',
            replace_existing=True
        )
        
        # Add cleanup job - run every 24 hours
        cls._scheduler.add_job(
            cls.cleanup_job,
            IntervalTrigger(hours=24),
            id='cleanup_news',
            replace_existing=True
        )
        
        cls._scheduler.start()
        logger.info("News sync scheduler started")
        
    @classmethod
    def stop_scheduler(cls):
        """Stop the background scheduler"""
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown()
            logger.info("News sync scheduler stopped")

    @staticmethod
    async def sync_job():
        """Background job to sync news"""
        logger.info("Starting scheduled news sync")
        db = SessionLocal()
        try:
            # Sync news (fetch 2 pages for regular updates)
            await NewsService.sync_news_from_api(db, max_pages=2)
            logger.info("Scheduled news sync completed successfully")
        except Exception as e:
            logger.error(f"Scheduled news sync failed: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def cleanup_job():
        """Background job to clean up old news"""
        logger.info("Starting scheduled news cleanup")
        db = SessionLocal()
        try:
            # Remove articles not seen for 7 days
            count = NewsService.cleanup_deleted_news(db, days=7)
            logger.info(f"Scheduled news cleanup completed. Removed {count} articles")
        except Exception as e:
            logger.error(f"Scheduled news cleanup failed: {str(e)}")
        finally:
            db.close()
