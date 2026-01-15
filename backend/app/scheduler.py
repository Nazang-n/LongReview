"""
Sentiment Cache Scheduler

Automatically updates game sentiment data and review tags from Steam API every hour.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
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

def update_review_tags(update_existing: bool = True):
    """
    Update review tags for games that need refresh.
    
    Args:
        update_existing: If True, updates tags older than 7 days. If False, only updates games with NO tags.
    """
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
        print(f"[Review Tags Scheduler] Checking {len(games)} games for tag updates (update_existing={update_existing})...")
        
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
                elif update_existing:
                    age = datetime.now() - existing_tags.updated_at.replace(tzinfo=None)
                    if age > timedelta(days=7):
                        needs_update = True
                        print(f"[Review Tags] Game {game.id} ({game.title}) tags are {age.days} old, refreshing...")
                
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
                    time.sleep(5)
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

def import_newest_games():
    """Import newest games from Steam (daily task)"""
    db = SessionLocal()
    stats = {
        'imported': 0,
        'skipped': 0,
        'failed': 0,
        'errors': 0
    }
    
    try:
        print("[Newest Games Scheduler] Starting import of newest games...")
        
        # Import 20 newest games daily
        newest_games = SteamAPIClient.get_newest_games_from_steam_store(limit=20)
        
        if not newest_games:
            print("[Newest Games Scheduler] No games fetched from Steam")
            return stats
        
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        
        for game in newest_games:
            app_id = game.get('app_id')
            
            if not app_id:
                continue
            
            try:
                # Check if game already exists
                existing_game = db.query(models.Game).filter(
                    models.Game.steam_app_id == int(app_id)
                ).first()
                
                if existing_game:
                    skipped_count += 1
                    continue
                
                # Fetch detailed info from Steam API
                steam_details_en = SteamAPIClient.get_app_details(int(app_id), language="english", country_code="us")
                
                if not steam_details_en:
                    failed_count += 1
                    continue
                
                # Fetch Thai version
                steam_details_th = SteamAPIClient.get_app_details(int(app_id), language="thai", country_code="th")
                
                # Import utilities
                from .utils.translator import translator
                from .utils.text_cleaner import clean_html_text
                
                # Get descriptions
                english_desc = None
                thai_desc = None
                
                if steam_details_en.get('about_the_game'):
                    english_desc = clean_html_text(steam_details_en.get('about_the_game'))
                elif steam_details_en.get('short_description'):
                    english_desc = clean_html_text(steam_details_en.get('short_description'))
                
                if steam_details_th and steam_details_th.get('about_the_game'):
                    cleaned_thai = clean_html_text(steam_details_th.get('about_the_game'))
                    if translator.detect_language(cleaned_thai) == 'th':
                        thai_desc = cleaned_thai
                
                if not thai_desc and english_desc:
                    try:
                        thai_desc = translator.translate_to_thai(english_desc)
                    except:
                        pass
                
                # Extract platform info
                platforms = steam_details_en.get('platforms', {})
                platform_list = []
                if platforms.get('windows'): platform_list.append('Windows')
                if platforms.get('mac'): platform_list.append('Mac')
                if platforms.get('linux'): platform_list.append('Linux')
                platform_str = ', '.join(platform_list) if platform_list else None
                
                # Extract price
                price_overview = steam_details_en.get('price_overview', {})
                price_str = price_overview.get('final_formatted') if price_overview else None
                
                # Extract video
                movies = steam_details_en.get('movies', [])
                video_url = None
                if movies:
                    video_url = movies[0].get('webm', {}).get('480') or movies[0].get('mp4', {}).get('480')
                
                # Parse release date
                release_date_info = steam_details_en.get('release_date', {})
                release_date_str = release_date_info.get('date')
                coming_soon = release_date_info.get('coming_soon', False)
                release_date_obj = None
                
                if release_date_str and not coming_soon:
                    date_formats = [
                        '%d %b, %Y', '%b %d, %Y', '%d %B, %Y', '%B %d, %Y',
                        '%Y-%m-%d', '%d %b %Y', '%b %d %Y', '%Y'
                    ]
                    for fmt in date_formats:
                        try:
                            release_date_obj = datetime.strptime(release_date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                
                # Create new game
                new_game = models.Game(
                    title=steam_details_en.get("name"),
                    description=english_desc,
                    about_game_th=thai_desc,
                    genre=", ".join([g["description"] for g in steam_details_en.get("genres", [])[:3]]),
                    image_url=steam_details_en.get("header_image"),
                    release_date=release_date_obj,
                    developer=", ".join(steam_details_en.get("developers", [])),
                    publisher=", ".join(steam_details_en.get("publishers", [])),
                    platform=platform_str,
                    price=price_str,
                    video=video_url,
                    steam_app_id=int(app_id)
                )
                
                db.add(new_game)
                db.flush()
                
                # Auto-tag player modes and genres
                try:
                    categories = steam_details_en.get('categories', [])
                    for category in categories:
                        cat_id = category.get('id')
                        mode_name = None
                        if cat_id == 2: mode_name = 'Single-player'
                        elif cat_id == 1: mode_name = 'Multi-player'
                        elif cat_id in [9, 24, 36, 37, 38]: mode_name = 'Co-op'
                        
                        if mode_name:
                            tag = db.query(models.Tag).filter(models.Tag.name == mode_name, models.Tag.type == 'player_mode').first()
                            if not tag:
                                tag = models.Tag(name=mode_name, type='player_mode')
                                db.add(tag)
                                db.flush()
                            game_tag = models.GameTag(game_id=new_game.id, tag_id=tag.id)
                            db.add(game_tag)
                    
                    genres = steam_details_en.get('genres', [])
                    for genre_data in genres:
                        genre_name = genre_data.get('description')
                        if genre_name:
                            genre_tag = db.query(models.Tag).filter(models.Tag.name == genre_name, models.Tag.type == 'genre').first()
                            if not genre_tag:
                                genre_tag = models.Tag(name=genre_name, type='genre')
                                db.add(genre_tag)
                                db.flush()
                            game_tag = models.GameTag(game_id=new_game.id, tag_id=genre_tag.id)
                            db.add(game_tag)
                except Exception as e:
                    print(f"[Newest Games] Error tagging game: {e}")
                
                # Fetch sentiment and Thai reviews
                try:
                    from .utils.sentiment_helper import fetch_and_cache_sentiment
                    fetch_and_cache_sentiment(new_game.id, int(app_id), db)
                except:
                    pass
                
                try:
                    from .utils.thai_review_helper import fetch_and_cache_thai_reviews
                    fetch_and_cache_thai_reviews(new_game.id, int(app_id), db, max_reviews=50)
                except:
                    pass
                
                db.commit()
                imported_count += 1
                print(f"[Newest Games] ✓ Imported: {new_game.title}")
                
                time.sleep(1.5)
                
            except Exception as e:
                print(f"[Newest Games] Error importing game {app_id}: {e}")
                failed_count += 1
                db.rollback()
                continue
        
        stats['imported'] = imported_count
        stats['skipped'] = skipped_count
        stats['failed'] = failed_count
        
        print(f"[Newest Games Scheduler] Complete! Imported: {imported_count}, Skipped: {skipped_count}, Failed: {failed_count}")
        return stats
        
    except Exception as e:
        print(f"[Newest Games Scheduler] Fatal error: {e}")
        stats['errors'] = 1
        return stats
    finally:
        db.close()

def cleanup_password_reset_tokens():
    """Delete expired, used, and old password reset tokens (daily cleanup)"""
    db = SessionLocal()
    stats = {
        'total_deleted': 0,
        'expired_deleted': 0,
        'used_deleted': 0,
        'old_deleted': 0,
        'errors': 0
    }
    
    try:
        from datetime import timedelta
        
        print("[Token Cleanup] Starting password reset token cleanup...")
        
        # Delete expired tokens
        expired_count = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.expires_at < datetime.utcnow()
        ).delete(synchronize_session=False)
        stats['expired_deleted'] = expired_count
        
        # Delete used tokens
        used_count = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.used == True
        ).delete(synchronize_session=False)
        stats['used_deleted'] = used_count
        
        # Delete old tokens (>7 days)
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        old_count = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.created_at < cutoff_date
        ).delete(synchronize_session=False)
        stats['old_deleted'] = old_count
        
        db.commit()
        
        stats['total_deleted'] = expired_count + used_count + old_count
        
        print(f"[Token Cleanup] Complete! Deleted {stats['total_deleted']} tokens:")
        print(f"  - Expired: {expired_count}")
        print(f"  - Used: {used_count}")
        print(f"  - Old (>7 days): {old_count}")
        
        return stats
        
    except Exception as e:
        print(f"[Token Cleanup] Error: {e}")
        stats['errors'] = 1
        db.rollback()
        return stats
    finally:
        db.close()

# Initialize scheduler
scheduler = BackgroundScheduler()

# Import newest games job (daily at 12:00 AM)
scheduler.add_job(
    func=import_newest_games,
    trigger=CronTrigger(hour=0, minute=0),
    id='import_newest_games',
    name='Import newest games from Steam',
    replace_existing=True
)

# Sentiment update job (daily at 12:30 AM)
scheduler.add_job(
    func=update_all_sentiments,
    trigger=CronTrigger(hour=0, minute=30),
    id='update_sentiments',
    name='Update game sentiments from Steam API',
    replace_existing=True
)

# Review tags update job (daily at 1:00 AM)
scheduler.add_job(
    func=update_review_tags,
    trigger=CronTrigger(hour=1, minute=0),
    id='update_review_tags',
    name='Update game review tags from Steam reviews',
    replace_existing=True
)

# Password reset token cleanup job (daily at 2:00 AM)
scheduler.add_job(
    func=cleanup_password_reset_tokens,
    trigger=CronTrigger(hour=2, minute=0),
    id='cleanup_password_tokens',
    name='Clean up expired and old password reset tokens',
    replace_existing=True
)

def start_scheduler():
    """Start the background scheduler"""
    if not scheduler.running:
        scheduler.start()
        print("[Scheduler] Started - All jobs run daily: Newest games (12:00 AM), Sentiment (12:30 AM), Review tags (1:00 AM), Token cleanup (2:00 AM)")

def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Stopped")
