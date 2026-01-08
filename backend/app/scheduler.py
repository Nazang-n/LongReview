"""
Sentiment Cache Scheduler

Automatically updates game sentiment data from Steam API every hour.
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
    try:
        # Get all games with steam_app_id
        games = db.query(models.Game).filter(
            models.Game.steam_app_id.isnot(None)
        ).all()
        
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
        
        print(f"[Sentiment Scheduler] Update complete! Updated: {updated_count}, Errors: {error_count}")
        
    except Exception as e:
        print(f"[Sentiment Scheduler] Fatal error: {e}")
    finally:
        db.close()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=update_all_sentiments,
    trigger=IntervalTrigger(hours=1),
    id='update_sentiments',
    name='Update game sentiments from Steam API',
    replace_existing=True
)

def start_scheduler():
    """Start the background scheduler"""
    if not scheduler.running:
        scheduler.start()
        print("[Sentiment Scheduler] Started - will update every hour")

def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Sentiment Scheduler] Stopped")
