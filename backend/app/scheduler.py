"""
Sentiment Cache Scheduler

Automatically updates game sentiment data and review tags from Steam API every hour.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from .database import SessionLocal
from .steam_api import SteamAPIClient
from . import models
from datetime import datetime
import time

def update_all_sentiments():
    """Update sentiment for all games with steam_app_id"""
    db = SessionLocal()
    stats = {
        'games_processed': 0,
        'updated': 0,
        'errors': 0
    }
    try:
        # Get all games with steam_app_id
        games = db.query(models.Game).filter(
            models.Game.steam_app_id.isnot(None)
        ).all()
        
        stats['games_processed'] = len(games)
        print(f"[Sentiment Scheduler] Starting update for {len(games)} games...")
        updated_count = 0
        error_count = 0
        
        for game in games:
            try:
                # Fetch from Steam API
                review_summary = SteamAPIClient.get_app_reviews(
                    app_id=int(game.steam_app_id),
                    language="all",
                    num_per_page=0
                )
                
                if review_summary and review_summary.get("success") == 1:
                    summary = review_summary.get("query_summary", {})
                    total = summary.get("total_reviews", 0)
                    positive = summary.get("total_positive", 0)
                    negative = summary.get("total_negative", 0)
                    review_score_desc = summary.get("review_score_desc", "No user reviews")
                    
                    # Calculate percentages
                    if total > 0:
                        pos_pct = round((positive / total * 100), 1)
                        neg_pct = round((negative / total * 100), 1)
                    else:
                        pos_pct = 0
                        neg_pct = 0
                    
                    # Find or create sentiment record in game_sentiment table
                    sentiment = db.query(models.GameSentiment).filter(
                        models.GameSentiment.game_id == game.id
                    ).first()
                    
                    if sentiment:
                        # Update existing sentiment record
                        sentiment.positive_percent = pos_pct
                        sentiment.negative_percent = neg_pct
                        sentiment.total_reviews = total
                        sentiment.review_score_desc = review_score_desc
                        sentiment.last_updated = datetime.utcnow()
                    else:
                        # Create new sentiment record
                        sentiment = models.GameSentiment(
                            game_id=game.id,
                            positive_percent=pos_pct,
                            negative_percent=neg_pct,
                            total_reviews=total,
                            review_score_desc=review_score_desc,
                            last_updated=datetime.utcnow()
                        )
                        db.add(sentiment)
                    
                    # Update Game rating (0-10 scale)
                    game.rating = round(pos_pct / 10.0, 1)
                    
                    db.commit()
                    updated_count += 1
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"[Sentiment Scheduler] Error updating game {game.id} ({game.title}): {e}")
                error_count += 1
                continue
        
        stats['updated'] = updated_count
        stats['errors'] = error_count
        
        print(f"[Sentiment Scheduler] Update complete! Updated: {updated_count}, Errors: {error_count}")
        return stats
        
    except Exception as e:
        print(f"[Sentiment Scheduler] Fatal error: {e}")
    finally:
        db.close()

def update_review_tags():
    """Update review tags for games that need refresh (older than 7 days or no tags)"""
    db = SessionLocal()
    stats = {
        'games_checked': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    try:
        from .services.review_tags_service import ReviewTagsService
        from datetime import timedelta
        
        # Get all games with steam_app_id
        games = db.query(models.Game).filter(
            models.Game.steam_app_id.isnot(None)
        ).all()
        
        stats['games_checked'] = len(games)
        print(f"[Review Tags Scheduler] Checking {len(games)} games for tag updates...")
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for game in games:
            try:
                # Check if tags exist and are recent
                existing_tags = db.query(models.GameReviewTag).filter(
                    models.GameReviewTag.game_id == game.id
                ).first()
                
                needs_update = False
                if not existing_tags:
                    needs_update = True
                    print(f"[Review Tags] Game {game.id} ({game.title}) has no tags, generating...")
                else:
                    age = datetime.now() - existing_tags.updated_at.replace(tzinfo=None)
                    if age > timedelta(days=7):
                        needs_update = True
                        print(f"[Review Tags] Game {game.id} ({game.title}) tags are {age.days} days old, refreshing...")
                
                if needs_update:
                    tags_service = ReviewTagsService(db)
                    result = tags_service.generate_tags_for_game(game.id, top_n=10, max_reviews=1500)
                    
                    if result.get('success'):
                        updated_count += 1
                        print(f"[Review Tags] ✓ Updated tags for {game.title}")
                    else:
                        error_count += 1
                        print(f"[Review Tags] ✗ Failed to update {game.title}: {result.get('error')}")
                    
                    # Delay to avoid overwhelming the API
                    time.sleep(2)
                else:
                    skipped_count += 1
                    
            except Exception as e:
                print(f"[Review Tags Scheduler] Error updating game {game.id} ({game.title}): {e}")
                error_count += 1
                continue
        
        stats['updated'] = updated_count
        stats['skipped'] = skipped_count
        stats['errors'] = error_count
        
        print(f"[Review Tags Scheduler] Update complete! Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}")
        return stats
        
    except Exception as e:
        print(f"[Review Tags Scheduler] Fatal error: {e}")
        raise
    finally:
        db.close()

# Initialize scheduler
scheduler = BackgroundScheduler()

# Sentiment update job (every hour)
scheduler.add_job(
    func=update_all_sentiments,
    trigger=IntervalTrigger(hours=1),
    id='update_sentiments',
    name='Update game sentiments from Steam API',
    replace_existing=True
)

# Review tags update job (every hour, offset by 30 minutes)
scheduler.add_job(
    func=update_review_tags,
    trigger=IntervalTrigger(hours=1),
    id='update_review_tags',
    name='Update game review tags from Steam reviews',
    replace_existing=True
)

def start_scheduler():
    """Start the background scheduler"""
    if not scheduler.running:
        scheduler.start()
        print("[Scheduler] Started - Sentiment updates every hour, Review tags every hour")

def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Stopped")
