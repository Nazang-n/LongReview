"""
Thai Review Fetching Scheduler
Runs hourly to fetch Thai reviews from Steam for display in game detail pages
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def update_thai_reviews():
    """
    Hourly job to fetch Thai reviews from Steam for games
    Stores reviews in the 'review' table for display in game detail pages
    """
    from ..database import SessionLocal
    from ..steam_api import SteamAPIClient
    from .. import models
    
    logger.info("=" * 60)
    logger.info(f"Starting Thai review update job at {datetime.now()}")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Get games that need review updates (not fetched or >24 hours old)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        games_to_update = db.query(models.Game).filter(
            (models.Game.last_review_fetch == None) | (models.Game.last_review_fetch < cutoff_time),
            models.Game.steam_app_id != None
        ).order_by(
            models.Game.last_review_fetch.asc().nullsfirst()
        ).limit(10).all()
        
        if not games_to_update:
            logger.info("No games need review updates")
            return
        
        logger.info(f"Found {len(games_to_update)} games needing Thai review updates")
        
        total_new_reviews = 0
        successful_updates = 0
        failed_updates = 0
        
        for game in games_to_update:
            try:
                logger.info(f"Fetching Thai reviews for: {game.title} (ID: {game.id}, Steam: {game.steam_app_id})")
                
                # Fetch Thai reviews from Steam
                steam_reviews = SteamAPIClient.get_all_reviews(
                    app_id=int(game.steam_app_id),
                    language="thai",
                    max_reviews=50  # Limit to 50 Thai reviews per game to reduce memory usage
                )
                
                if not steam_reviews:
                    logger.info(f"  ℹ No Thai reviews found for {game.title}")
                    # Still update timestamp to avoid retrying immediately
                    game.last_review_fetch = datetime.now()
                    db.commit()
                    continue
                
                logger.info(f"  📊 Fetched {len(steam_reviews)} Thai reviews from Steam")

                # Filter for valid Thai content (strict check)
                from ..utils.thai_validator import is_valid_thai_content
                steam_reviews = [r for r in steam_reviews if is_valid_thai_content(r.get('review', ''))]
                logger.info(f"  🔍 Valid Thai reviews after content check: {len(steam_reviews)}")
                
                imported_count = 0
                skipped_count = 0
                
                for steam_review in steam_reviews:
                    try:
                        recommendation_id = steam_review.get('recommendationid')
                        
                        # Check if review already exists
                        existing = db.query(models.Review).filter(
                            models.Review.steam_id == recommendation_id
                        ).first()
                        
                        if existing:
                            skipped_count += 1
                            continue
                        
                        # Extract review data
                        created_timestamp = steam_review.get('timestamp_created')
                        created_at = datetime.fromtimestamp(created_timestamp) if created_timestamp else None
                        author = steam_review.get('author', {})
                        playtime_minutes = author.get("playtime_at_review", 0)
                        playtime_hours = round(playtime_minutes / 60, 1) if playtime_minutes else 0
                        
                        # Create new review
                        new_review = models.Review(
                            game_id=game.id,
                            steam_id=recommendation_id,
                            content=steam_review.get('review', ''),
                            owner=f"Steam User {author.get('steamid', 'Unknown')[-4:]}",
                            voted_up=steam_review.get('voted_up', True),
                            created_at=created_at,
                            is_steam_review=True,
                            steam_author=author.get('steamid', 'Unknown'),
                            helpful_count=steam_review.get('votes_up', 0),
                            playtime_hours=playtime_hours
                        )
                        
                        db.add(new_review)
                        db.commit()  # Commit each review individually to avoid bulk duplicate errors
                        imported_count += 1
                        
                    except Exception as e:
                        logger.error(f"  ✗ Error importing review {recommendation_id}: {e}")
                        db.rollback()  # Rollback this specific review
                        continue
                
                # Update last fetch timestamp
                game.last_review_fetch = datetime.now()
                db.commit()
                
                total_new_reviews += imported_count
                successful_updates += 1
                logger.info(f"  ✓ Imported {imported_count} new Thai reviews (skipped {skipped_count} duplicates)")
                
            except Exception as e:
                failed_updates += 1
                logger.error(f"  ✗ Error updating {game.title}: {e}")
                db.rollback()
                continue
        
        logger.info("=" * 60)
        logger.info(f"Thai review update complete:")
        logger.info(f"  - Games processed: {len(games_to_update)}")
        logger.info(f"  - Successful: {successful_updates}")
        logger.info(f"  - Failed: {failed_updates}")
        logger.info(f"  - Total new reviews: {total_new_reviews}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in Thai review update job: {e}")
        db.rollback()
    finally:
        db.close()


def start_review_scheduler():
    """
    Start the background scheduler for hourly Thai review updates
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    scheduler = BackgroundScheduler()
    
    # Schedule hourly Thai review update (every hour at minute 0)
    scheduler.add_job(
        update_thai_reviews,
        trigger=CronTrigger(minute=0),  # Every hour at :00
        id='hourly_thai_review_update',
        name='Hourly Thai Review Update',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✓ Thai review scheduler started - Updates every hour")
    
    # Log next run time
    next_run = scheduler.get_job('hourly_thai_review_update').next_run_time
    logger.info(f"  Next Thai review update scheduled for: {next_run}")


def stop_review_scheduler():
    """Stop the review scheduler"""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Thai review scheduler stopped")


def trigger_manual_update(force_update: bool = False, limit: int = 0):
    """
    Manually trigger a Thai review update (for admin panel or nightly scheduler)
    Returns statistics about the update
    
    Args:
        force_update: If True, update all games regardless of last fetch time.
                      If False, skip games updated in last 24h.
        limit: Max number of games to process. 0 = no limit (process all).
               Used by the nightly scheduler to cap at 50 games/night.
    """
    logger.info(f"🔧 Thai review update triggered (force={force_update}, limit={limit if limit > 0 else 'all'})")
    
    from ..database import SessionLocal
    from ..steam_api import SteamAPIClient
    from .. import models
    from datetime import timedelta
    
    db = SessionLocal()
    stats = {
        'games_processed': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'total_new_reviews': 0
    }
    
    try:
        query = db.query(models.Game).filter(
            models.Game.steam_app_id != None
        ).order_by(
            models.Game.last_review_fetch.asc().nullsfirst()
        )
        
        if limit > 0:
            query = query.limit(limit)
        
        games_to_update = query.all()
        stats['games_processed'] = len(games_to_update)
        
        for game in games_to_update:
            try:
                # Check for smart update skipping
                if not force_update and game.last_review_fetch:
                    # Strip tzinfo so naive datetime.now() can be compared with
                    # timezone-aware datetimes that may be stored in the DB
                    last_fetch = game.last_review_fetch.replace(tzinfo=None)
                    age = datetime.utcnow() - last_fetch
                    if age < timedelta(hours=24):
                        stats['skipped'] += 1
                        continue
                
                logger.info(f"Fetching Thai reviews for: {game.title}")
                
                steam_reviews = SteamAPIClient.get_all_reviews(
                    app_id=int(game.steam_app_id),
                    language="thai",
                    max_reviews=50  # 50 reviews/game to reduce memory usage
                )
                
                 # Filter for valid Thai content (strict check)
                from ..utils.thai_validator import is_valid_thai_content
                if steam_reviews:
                    steam_reviews = [r for r in steam_reviews if is_valid_thai_content(r.get('review', ''))]
                
                if not steam_reviews:
                    game.last_review_fetch = datetime.now()
                    db.commit()
                    continue
                
                imported_count = 0
                
                for steam_review in steam_reviews:
                    try:
                        recommendation_id = steam_review.get('recommendationid')
                        
                        existing = db.query(models.Review).filter(
                            models.Review.steam_id == recommendation_id
                        ).first()
                        
                        if existing:
                            continue
                        
                        created_timestamp = steam_review.get('timestamp_created')
                        created_at = datetime.fromtimestamp(created_timestamp) if created_timestamp else None
                        author = steam_review.get('author', {})
                        playtime_minutes = author.get("playtime_at_review", 0)
                        playtime_hours = round(playtime_minutes / 60, 1) if playtime_minutes else 0
                        
                        new_review = models.Review(
                            game_id=game.id,
                            steam_id=recommendation_id,
                            content=steam_review.get('review', ''),
                            owner=f"Steam User {author.get('steamid', 'Unknown')[-4:]}",
                            voted_up=steam_review.get('voted_up', True),
                            created_at=created_at,
                            is_steam_review=True,
                            steam_author=author.get('steamid', 'Unknown'),
                            helpful_count=steam_review.get('votes_up', 0),
                            playtime_hours=playtime_hours
                        )
                        
                        db.add(new_review)
                        db.commit()
                        imported_count += 1
                        
                    except Exception as e:
                        logger.error(f"  ✗ Error importing review: {e}")
                        db.rollback()
                        continue
                
                game.last_review_fetch = datetime.now()
                db.commit()
                
                stats['total_new_reviews'] += imported_count
                stats['successful'] += 1
                
            except Exception as e:
                stats['failed'] += 1
                logger.error(f"  ✗ Error updating {game.title}: {e}")
                db.rollback()
                continue
        
        logger.info("=" * 60)
        logger.info(f"Thai review update complete:")
        logger.info(f"  - Games processed: {stats['games_processed']}")
        logger.info(f"  - Successful: {stats['successful']}")
        logger.info(f"  - Failed: {stats['failed']}")
        logger.info(f"  - Total new reviews: {stats['total_new_reviews']}")
        logger.info("=" * 60)
        logger.info("Manual Thai review update completed successfully")
        
        # Log the update to daily_update_log
        try:
            from datetime import datetime, timedelta
            from ..models import DailyUpdateLog
            
            today = (datetime.utcnow() + timedelta(hours=7)).date()
            status = 'success'
            if stats['failed'] > 0 and stats['successful'] == 0:
                status = 'failed'
            elif stats['failed'] > 0:
                status = 'partial'
            
            log_entry = DailyUpdateLog(
                update_type='reviews',
                update_date=today,
                status=status,
                items_processed=stats['games_processed'],
                items_successful=stats['successful'],
                items_failed=stats['failed']
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging review update: {e}")
            db.rollback()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error in manual Thai review update: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()
