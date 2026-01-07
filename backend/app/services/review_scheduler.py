"""
Daily review update scheduler
Runs at 12 AM daily to fetch new reviews for games
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def update_game_reviews():
    """
    Daily job to update reviews for games
    Runs at 12 AM every day
    """
    from ..database import SessionLocal
    from ..services.review_service import review_service
    
    logger.info("=" * 60)
    logger.info(f"Starting daily review update job at {datetime.now()}")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Get games that need review updates (not fetched or > 24 hours old)
        # Reduced to 10 games per run for faster processing
        games_to_update = review_service.get_games_needing_review_update(db, limit=10)
        
        if not games_to_update:
            logger.info("No games need review updates")
            return
        
        logger.info(f"Found {len(games_to_update)} games needing review updates")
        
        total_new_reviews = 0
        successful_updates = 0
        failed_updates = 0
        
        for game in games_to_update:
            try:
                logger.info(f"Updating reviews for: {game.title} (ID: {game.id})")
                
                result = review_service.fetch_and_store_reviews(
                    db=db,
                    game_id=game.id,
                    steam_app_id=game.steam_app_id
                    # No max_reviews limit - fetch all reviews during daily update
                )
                
                if result.get("success"):
                    new_reviews = result.get("new_reviews", 0)
                    total_new_reviews += new_reviews
                    successful_updates += 1
                    logger.info(f"  ✓ Fetched {new_reviews} new reviews")
                else:
                    failed_updates += 1
                    logger.warning(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                failed_updates += 1
                logger.error(f"  ✗ Error updating {game.title}: {e}")
                continue
        
        logger.info("=" * 60)
        logger.info(f"Daily review update complete:")
        logger.info(f"  - Games processed: {len(games_to_update)}")
        logger.info(f"  - Successful: {successful_updates}")
        logger.info(f"  - Failed: {failed_updates}")
        logger.info(f"  - Total new reviews: {total_new_reviews}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in daily review update job: {e}")
    finally:
        db.close()


def start_review_scheduler():
    """
    Start the background scheduler for hourly review updates
    Runs every hour to fetch reviews for newly imported games
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    scheduler = BackgroundScheduler()
    
    # Schedule hourly review update (every hour at minute 0)
    scheduler.add_job(
        update_game_reviews,
        trigger=CronTrigger(minute=0),  # Every hour at :00
        id='hourly_review_update',
        name='Hourly Review Update',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✓ Review scheduler started - Hourly updates every hour")
    
    # Log next run time
    next_run = scheduler.get_job('hourly_review_update').next_run_time
    logger.info(f"  Next review update scheduled for: {next_run}")


def stop_review_scheduler():
    """Stop the review scheduler"""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Review scheduler stopped")


def trigger_manual_update():
    """
    Manually trigger a review update (for testing)
    """
    logger.info("Manual review update triggered")
    try:
        update_game_reviews()
        logger.info("Manual review update completed successfully")
    except Exception as e:
        logger.error(f"Error in manual review update: {e}")
        import traceback
        traceback.print_exc()
        raise
