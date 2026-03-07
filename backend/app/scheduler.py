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
from datetime import datetime, date, timedelta
import time
import json

def log_daily_update(db: Session, update_type: str, stats: dict, game_id: int = None):
    """Helper function to log daily update operations"""
    try:
        from datetime import datetime, timedelta
        today = (datetime.utcnow() + timedelta(hours=7)).date()
        
        # Determine status based on stats
        status = 'success'
        items_processed = stats.get('games_processed', 0) or stats.get('total_processed', 0) or stats.get('imported', 0) or stats.get('skipped', 0)
        # Prioritize 'added' over 'updated' so news updates show new articles count
        items_successful = stats.get('added', 0) or stats.get('games_successful', 0) or stats.get('updated', 0) or stats.get('imported', 0)
        items_failed = stats.get('errors', 0) or stats.get('failed', 0) or stats.get('games_failed', 0)
        
        if items_failed > 0 and items_successful == 0 and items_processed > 0:
            status = 'failed'
        elif items_failed > 0:
            status = 'partial'
        
        # Create log entry
        log_entry = models.DailyUpdateLog(
            update_type=update_type,
            update_date=today,
            status=status,
            items_processed=items_processed,
            items_successful=items_successful,
            items_failed=items_failed,
            game_id=game_id
        )
        
        db.add(log_entry)
        db.commit()
        print(f"[Daily Update Log] Logged {update_type} update: {status}")
    except Exception as e:
        print(f"[Daily Update Log] Error logging update: {e}")
        db.rollback()

def cleanup_old_daily_logs():
    """
    Clean up old daily update logs, keeping only today's logs.
    This runs daily to reset the status dashboard.
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        today = (datetime.utcnow() + timedelta(hours=7)).date()
        
        # Delete all logs that are not from today
        deleted = db.query(models.DailyUpdateLog).filter(
            models.DailyUpdateLog.update_date < today
        ).delete()
        
        db.commit()
        print(f"[Daily Log Cleanup] Deleted {deleted} old log entries")
    except Exception as e:
        print(f"[Daily Log Cleanup] Error: {e}")
        db.rollback()
    finally:
        db.close()

def update_all_sentiments(force_update: bool = False):
    """
    Update sentiment for all games, processed in chunks to stay within Render's 512 MB RAM.
    
    Args:
        force_update: If True, update all games regardless of last_updated time.
                      If False, only update games not updated in the last 24 hours.
    """
    db = SessionLocal()
    stats = {
        'games_processed': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    CHUNK_SIZE = 30  # Process 30 games at a time to keep RAM low
    try:
        # Count total games
        total_games = db.query(models.Game).filter(
            models.Game.steam_app_id.isnot(None)
        ).count()
        
        stats['games_processed'] = total_games
        print(f"[Sentiment Scheduler] Starting update for {total_games} games in chunks of {CHUNK_SIZE} (force={force_update})...")
        updated_count = 0
        skipped_count = 0
        error_count = 0
        offset = 0

        while offset < total_games:
            # Load one chunk
            games = db.query(models.Game).filter(
                models.Game.steam_app_id.isnot(None)
            ).order_by(models.Game.id).offset(offset).limit(CHUNK_SIZE).all()

            if not games:
                break

            for game in games:
                try:
                    # Check if we should skip
                    if not force_update:
                        sentiment = db.query(models.GameSentiment).filter(
                            models.GameSentiment.game_id == game.id
                        ).first()
                        
                        if sentiment and sentiment.last_updated:
                            age = datetime.utcnow() - sentiment.last_updated.replace(tzinfo=None)
                            if age < timedelta(hours=24):
                                skipped_count += 1
                                continue
                    
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
                        
                        if total > 0:
                            pos_pct = round((positive / total * 100), 1)
                            neg_pct = round((negative / total * 100), 1)
                        else:
                            pos_pct = 0
                            neg_pct = 0
                        
                        sentiment = db.query(models.GameSentiment).filter(
                            models.GameSentiment.game_id == game.id
                        ).first()
                        
                        if sentiment:
                            sentiment.positive_percent = pos_pct
                            sentiment.negative_percent = neg_pct
                            sentiment.total_reviews = total
                            sentiment.review_score_desc = review_score_desc
                            sentiment.last_updated = datetime.now()
                        else:
                            sentiment = models.GameSentiment(
                                game_id=game.id,
                                positive_percent=pos_pct,
                                negative_percent=neg_pct,
                                total_reviews=total,
                                review_score_desc=review_score_desc,
                                last_updated=datetime.now()
                            )
                            db.add(sentiment)
                        
                        game.rating = round(pos_pct / 10.0, 1)
                        db.commit()
                        updated_count += 1
                        time.sleep(0.5)
                        
                except Exception as e:
                    print(f"[Sentiment Scheduler] Error updating game {game.id} ({game.title}): {e}")
                    error_count += 1
                    continue

            # Free all ORM objects for this chunk before loading the next one
            db.expire_all()
            offset += CHUNK_SIZE
            print(f"[Sentiment Scheduler] Chunk done — offset {offset}/{total_games}, updated so far: {updated_count}")
        
        stats['updated'] = updated_count
        stats['errors'] = error_count
        log_daily_update(db, 'sentiment', stats)
        print(f"[Sentiment Scheduler] Update complete! Updated: {updated_count}, Errors: {error_count}")
        return stats
        
    except Exception as e:
        print(f"[Sentiment Scheduler] Fatal error: {e}")
    finally:
        db.close()

def update_review_tags(update_existing: bool = True):
    """
    Update review tags for games that need refresh, processed in chunks to stay within 512 MB RAM.
    
    Args:
        update_existing: If True, updates tags older than 7 days. If False, only updates games with NO tags.
    """
    db = SessionLocal()
    stats = {
        'games_processed': 0,  # renamed from games_checked for log_daily_update compatibility
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    CHUNK_SIZE = 30
    
    try:
        from .services.review_tags_service import ReviewTagsService
        from datetime import timedelta
        
        total_games = db.query(models.Game).filter(
            models.Game.steam_app_id.isnot(None)
        ).count()
        
        stats['games_processed'] = total_games
        print(f"[Review Tags Scheduler] Checking {total_games} games in chunks of {CHUNK_SIZE} (update_existing={update_existing})...")
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        offset = 0

        while offset < total_games:
            games = db.query(models.Game).filter(
                models.Game.steam_app_id.isnot(None)
            ).order_by(models.Game.id).offset(offset).limit(CHUNK_SIZE).all()

            if not games:
                break

            for game in games:
                try:
                    existing_tags = db.query(models.GameReviewTag).filter(
                        models.GameReviewTag.game_id == game.id,
                        models.GameReviewTag.tag_type.in_(['positive', 'negative'])
                    ).first()
                    
                    needs_update = False
                    if not existing_tags:
                        needs_update = True
                        print(f"[Review Tags] Game {game.id} ({game.title}) has no review tags, generating...")
                    elif update_existing:
                        age = datetime.now() - existing_tags.updated_at.replace(tzinfo=None)
                        if age > timedelta(days=7):
                            needs_update = True
                            print(f"[Review Tags] Game {game.id} ({game.title}) tags are {age.days} days old, refreshing...")
                    
                    if needs_update:
                        tags_service = ReviewTagsService(db)
                        result = tags_service.generate_tags_for_game(game.id, top_n=10, max_reviews=1500)
                        
                        if result.get('success'):
                            updated_count += 1
                            print(f"[Review Tags] [OK] Updated tags for {game.title}")
                        else:
                            error_count += 1
                            print(f"[Review Tags] [ERROR] Failed to update {game.title}: {result.get('error')}")
                        
                        time.sleep(5)
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    print(f"[Review Tags Scheduler] Error updating game {game.id} ({game.title}): {e}")
                    error_count += 1
                    continue

            # Free chunk from memory before loading next
            db.expire_all()
            offset += CHUNK_SIZE
            print(f"[Review Tags Scheduler] Chunk done — offset {offset}/{total_games}")
        
        stats['updated'] = updated_count
        stats['skipped'] = skipped_count
        stats['errors'] = error_count
        
        log_daily_update(db, 'tags', stats)
        print(f"[Review Tags Scheduler] Update complete! Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}")
        return stats
        
    except Exception as e:
        print(f"[Review Tags Scheduler] Fatal error: {e}")
        raise
    finally:
        db.close()

def import_newest_games(target_limit: int = 10):
    """Import newest games from Steam (daily task)
    
    Strategy:
      - ดึง candidates จาก Steam IStoreService (เรียงตาม last_modified)
      - กรอง: type=game, ไม่ใช่ coming_soon, release_date ใน N วัน
      - เช็คว่ามีใน DB แล้วหรือยัง (by steam_app_id)
      - 3-tier escalation ถ้าหาเกมใหม่ได้ไม่ถึง target:
          Tier 1: days_ago=60,  candidates=300
          Tier 2: days_ago=120, candidates=500
          Tier 3: days_ago=365, candidates=700
    """
    db = SessionLocal()
    stats = {
        'imported': 0,
        'skipped': 0,
        'failed': 0,
        'errors': 0,
        'imported_titles': []  # Track names of imported games
    }

    DATE_FORMATS = [
        '%d %b, %Y', '%b %d, %Y', '%d %B, %Y', '%B %d, %Y',
        '%Y-%m-%d', '%d %b %Y', '%b %d %Y', '%Y'
    ]

    def parse_release_date(date_str):
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None

    def import_single_game(app_id, imported_count, target_new_games, cutoff_date):
        """ดึงรายละเอียดและ import เกมเดียว — คืนค่า 'imported'/'skipped'/'failed'"""
        # เช็ค DB ก่อนเสมอ
        existing_game = db.query(models.Game).filter(
            models.Game.steam_app_id == int(app_id)
        ).first()
        if existing_game:
            return 'skipped'

        steam_details_en = SteamAPIClient.get_app_details(int(app_id), language="english", country_code="us")
        if not steam_details_en:
            # No details = likely a DLC, tool, or removed app — treat as skipped, not failed
            print(f"[Newest Games] Skipping {app_id}: no Steam details (likely DLC/tool/removed)")
            return 'skipped'

        # กรอง: ต้องเป็น game เท่านั้น
        if steam_details_en.get('type') not in ('game', None, ''):
            app_type = steam_details_en.get('type')
            if app_type and app_type != 'game':
                print(f"[Newest Games] Skipping {app_id}: type={app_type}")
                return 'skipped'

        # กรอง: ต้องไม่ใช่ coming_soon
        release_info = steam_details_en.get('release_date', {})
        if release_info.get('coming_soon'):
            print(f"[Newest Games] Skipping {app_id}: coming soon")
            return 'skipped'

        # กรอง: release_date ต้องอยู่ในช่วง cutoff และไม่ใช่วันในอนาคต
        release_date_str = release_info.get('date', '')
        release_date_obj = parse_release_date(release_date_str) if release_date_str else None
        today = datetime.now().date()
        if cutoff_date and release_date_obj and release_date_obj < cutoff_date:
            print(f"[Newest Games] Skipping {app_id}: released {release_date_str} (too old)")
            return 'skipped'
        if release_date_obj and release_date_obj > today:
            print(f"[Newest Games] Skipping {app_id}: future release ({release_date_str})")
            return 'skipped'

        # ดึง TH details
        steam_details_th = SteamAPIClient.get_app_details(int(app_id), language="thai", country_code="th")
        
        # Get price - prioritize THB from steam_details_th
        price_str = None
        
        # Check if game is free first
        if steam_details_th.get('is_free') or steam_details_en.get('is_free'):
            price_str = "Free"
            
        if not price_str and steam_details_th:
            price_overview_th = steam_details_th.get('price_overview', {})
            if price_overview_th:
                price_str = price_overview_th.get('final_formatted')
        
        # Fallback to USD if THB not found
        if not price_str:
            price_overview_en = steam_details_en.get('price_overview', {})
            if price_overview_en:
                price_str = price_overview_en.get('final_formatted')

        from .utils.translator import translator
        from .utils.text_cleaner import clean_html_text

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

        platforms = steam_details_en.get('platforms', {})
        platform_list = []
        if platforms.get('windows'): platform_list.append('Windows')
        if platforms.get('mac'): platform_list.append('Mac')
        if platforms.get('linux'): platform_list.append('Linux')
        platform_str = ', '.join(platform_list) if platform_list else None

        movies = steam_details_en.get('movies', [])
        videos_list = []
        for movie in movies:
            videos_list.append({
                "name": movie.get("name"),
                "thumbnail": movie.get("thumbnail"),
                "url": movie.get("dash_h264"),
                "hls_url": movie.get("hls_h264")
            })
        videos_json = json.dumps(videos_list) if videos_list else None

        screenshots = steam_details_en.get('screenshots', [])
        screenshots_list = []
        for ss in screenshots:
            screenshots_list.append({
                "id": ss.get("id"),
                "path_thumbnail": ss.get("path_thumbnail"),
                "path_full": ss.get("path_full")
            })
        screenshots_json = json.dumps(screenshots_list) if screenshots_list else None

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
            video=videos_json,
            screenshots=screenshots_json,
            steam_app_id=int(app_id)
        )

        db.add(new_game)
        db.flush()

        # Auto-tag player modes + genres
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
                    db.add(models.GameTag(game_id=new_game.id, tag_id=tag.id))

            genres = steam_details_en.get('genres', [])
            for genre_data in genres:
                genre_name = genre_data.get('description')
                if genre_name:
                    genre_tag = db.query(models.Tag).filter(models.Tag.name == genre_name, models.Tag.type == 'genre').first()
                    if not genre_tag:
                        genre_tag = models.Tag(name=genre_name, type='genre')
                        db.add(genre_tag)
                        db.flush()
                    db.add(models.GameTag(game_id=new_game.id, tag_id=genre_tag.id))
        except Exception as e:
            print(f"[Newest Games] Error tagging game: {e}")

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

        try:
            from .services.review_tags_service import ReviewTagsService
            tags_service = ReviewTagsService(db)
            print(f"[Newest Games] Generating review tags for {new_game.title}...")
            tags_service.generate_tags_for_game(new_game.id, top_n=10, max_reviews=1500)
        except Exception as e:
            print(f"[Newest Games] Warning: Failed to generate tags for {new_game.title}: {e}")

        db.commit()
        print(f"[Newest Games] Imported: {new_game.title} (release: {release_date_str})")
        return ('imported', new_game.title)

    try:
        print("[Newest Games Scheduler] Starting import of newest games...")

        target_new_games = target_limit
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        seen_app_ids = set()  # ป้องกัน import ซ้ำข้าม tier

        # 3-tier escalation: ขยาย days_ago และ candidates ถ้าได้เกมใหม่ไม่พอ
        tiers = [
            {'days_ago': 60,  'candidates': 300,  'label': 'Tier 1 (60 days, 300 candidates)'},
            {'days_ago': 120, 'candidates': 500,  'label': 'Tier 2 (120 days, 500 candidates)'},
            {'days_ago': 365, 'candidates': 700,  'label': 'Tier 3 (365 days, 700 candidates)'},
        ]

        for tier in tiers:
            if imported_count >= target_new_games:
                break

            days_ago = tier['days_ago']
            candidate_limit = tier['candidates']
            label = tier['label']
            cutoff_date = (datetime.now() - timedelta(days=days_ago)).date()

            print(f"[Newest Games] {label} — cutoff: {cutoff_date}")
            print(f"[Newest Games] Fetching {candidate_limit} candidates from Steam IStoreService...")

            candidates = SteamAPIClient.get_newest_released_games(candidate_limit=candidate_limit)

            if not candidates:
                print(f"[Newest Games] No candidates from Steam API, skipping {label}")
                continue

            print(f"[Newest Games] Got {len(candidates)} candidates, processing...")

            for game in candidates:
                if imported_count >= target_new_games:
                    print(f"[Newest Games] Target reached ({imported_count}/{target_new_games})!")
                    break

                app_id = game.get('app_id')
                if not app_id:
                    continue

                # ข้ามถ้าเคย process แล้วใน tier ก่อนหน้า
                if app_id in seen_app_ids:
                    continue
                seen_app_ids.add(app_id)

                try:
                    result = import_single_game(app_id, imported_count, target_new_games, cutoff_date)
                    # result is now a tuple ('imported', title) or a plain string
                    status = result[0] if isinstance(result, tuple) else result
                    if status == 'imported':
                        imported_count += 1
                        game_title = result[1] if isinstance(result, tuple) else None
                        if game_title:
                            stats['imported_titles'].append(game_title)
                        print(f"[Newest Games] Progress: {imported_count}/{target_new_games}")
                        time.sleep(1)
                    elif status == 'skipped':
                        skipped_count += 1
                    elif status == 'failed':
                        failed_count += 1
                except Exception as e:
                    print(f"[Newest Games] Error importing {app_id}: {e}")
                    failed_count += 1
                    db.rollback()

            print(f"[Newest Games] {label} done — imported so far: {imported_count}/{target_new_games}")

        stats['imported'] = imported_count
        stats['skipped'] = skipped_count
        stats['failed'] = failed_count

        log_daily_update(db, 'games', stats)

        print(f"[Newest Games] Complete! Imported: {imported_count}, Skipped: {skipped_count}, Failed: {failed_count}")
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
            models.PasswordResetToken.expires_at < datetime.now()
        ).delete(synchronize_session=False)
        stats['expired_deleted'] = expired_count
        
        # Delete used tokens
        used_count = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.used == True
        ).delete(synchronize_session=False)
        stats['used_deleted'] = used_count
        
        # Delete old tokens (>7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
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

# Daily log cleanup job (00:00 TH = 17:00 UTC)
scheduler.add_job(
    func=cleanup_old_daily_logs,
    trigger=CronTrigger(hour=17, minute=5),
    id='cleanup_daily_logs',
    name='Clean up old daily update logs',
    replace_existing=True,
    misfire_grace_time=86400 # 24 hours grace time for sleep/hibernate
)

# Import newest games job (00:05 TH = 17:05 UTC)
scheduler.add_job(
    func=import_newest_games,
    trigger=CronTrigger(hour=17, minute=10),
    id='import_newest_games',
    name='Import newest games from Steam',
    replace_existing=True,
    misfire_grace_time=86400
)

def update_news_daily():
    """Daily job to sync news and log status (wrapper for async service)"""
    print("[News Scheduler] Starting daily update...")
    import asyncio
    from .services.news_service import NewsService
    
    db = SessionLocal()
    stats = {
        'games_processed': 0, # Not applicable
        'updated': 0,
        'added': 0,
        'errors': 0
    }
    
    try:
        # Run async sync in sync context
        # BackgroundScheduler runs in a thread, so asyncio.run is safe
        result = asyncio.run(NewsService.sync_news_from_api(db, max_pages=4))
        
        if result.get('status') == 'success':
            stats['added'] = result.get('new_articles', 0)
            stats['updated'] = result.get('updated_articles', 0)
        else:
            stats['errors'] = 1
            
        # Log to daily_update_log
        log_daily_update(db, 'news', stats)
        print(f"[News Scheduler] Update complete! Added: {stats['added']}, Updated: {stats['updated']}")
        
    except Exception as e:
        print(f"[News Scheduler] Fatal error: {e}")
        stats['errors'] = 1
        log_daily_update(db, 'news', stats)
    finally:
        db.close()

# News update job (01:00 TH = 18:00 UTC)
scheduler.add_job(
    func=update_news_daily,
    trigger=CronTrigger(hour=18, minute=0),
    id='update_news',
    name='Update gaming news',
    replace_existing=True,
    misfire_grace_time=86400
)

def cleanup_old_news_daily():
    """Daily job to cleanup old news articles"""
    print("[News Cleanup Scheduler] Starting daily cleanup...")
    from .services.news_service import NewsService
    db = SessionLocal()
    try:
        # Mark articles not seen for 7 days as inactive
        count = NewsService.cleanup_deleted_news(db, days=7)
        print(f"[News Cleanup Scheduler] Cleanup complete. Marked {count} articles as inactive.")
    except Exception as e:
        print(f"[News Cleanup Scheduler] Fatal error: {e}")
    finally:
        db.close()

# News cleanup job (00:30 TH = 17:30 UTC)
scheduler.add_job(
    func=cleanup_old_news_daily,
    trigger=CronTrigger(hour=17, minute=30),
    id='cleanup_news',
    name='Clean up old news articles',
    replace_existing=True,
    misfire_grace_time=86400
)

# Sentiment update job (02:00 TH = 19:00 UTC)
scheduler.add_job(
    func=update_all_sentiments,
    trigger=CronTrigger(hour=19, minute=0),
    id='update_sentiments',
    name='Update game sentiments from Steam API',
    replace_existing=True,
    misfire_grace_time=86400,
    kwargs={'force_update': True}
)

# Review tags update job (03:00 TH = 20:00 UTC)
scheduler.add_job(
    func=update_review_tags,
    trigger=CronTrigger(hour=20, minute=0),
    id='update_review_tags',
    name='Update game review tags from Steam reviews',
    replace_existing=True,
    misfire_grace_time=86400
)

def update_thai_reviews_daily():
    """Daily job to update Thai reviews — processes games not updated in 24h, capped at 50/night to stay within 512 MB RAM"""
    print("[Thai Review Scheduler] Starting daily update (smart mode, max 50 games)...")
    try:
        from .services.review_scheduler import trigger_manual_update
        
        # Smart update — skip games already fetched within 24h, cap at 50 games/night
        stats = trigger_manual_update(force_update=False, limit=50)
        
        # Log to daily_update_log
        db = SessionLocal()
        try:
            log_daily_update(db, 'reviews', stats)
        finally:
            db.close()
            
    except Exception as e:
        print(f"[Thai Review Scheduler] Fatal error: {e}")

# Thai reviews update job (04:00 TH = 21:00 UTC)
scheduler.add_job(
    func=update_thai_reviews_daily,
    trigger=CronTrigger(hour=21, minute=0),
    id='update_thai_reviews',
    name='Update Thai reviews from Steam',
    replace_existing=True,
    misfire_grace_time=86400
)

# Token cleanup job (05:00 TH = 22:00 UTC)
scheduler.add_job(
    func=cleanup_password_reset_tokens,
    trigger=CronTrigger(hour=22, minute=0),
    id='cleanup_password_tokens',
    name='Clean up expired and old password reset tokens',
    replace_existing=True,
    misfire_grace_time=86400
)

def check_missed_daily_tasks():
    """Check if any daily tasks were missed and run them"""
    print("[Scheduler] Checking for missed daily tasks...")
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        th_time = datetime.utcnow() + timedelta(hours=7)
        today = th_time.date()
        
        # 1. Clean up logs if we are past 00:05 TH. 
        # (It's safe to run multiple times, it only deletes logs older than today)
        if th_time.hour > 0 or (th_time.hour == 0 and th_time.minute >= 5):
            print("[Scheduler] Running daily log cleanup check...")
            cleanup_old_daily_logs()
        
        # 2. Check 'games' import (Scheduled: 00:10 TH)
        if th_time.hour > 0 or (th_time.hour == 0 and th_time.minute >= 10):
            games_log = db.query(models.DailyUpdateLog).filter(
                models.DailyUpdateLog.update_type == 'games',
                models.DailyUpdateLog.update_date == today
            ).first()
            
            if not games_log:
                print("[Scheduler] Missed 'games' import. Scheduling now...")
                scheduler.add_job(
                    import_newest_games,
                    'date',
                    run_date=datetime.now() + timedelta(seconds=5),
                    id='catchup_games',
                    name='Catch-up: Import games'
                )

        # 3. Check 'news' update (Scheduled: 01:00 TH)
        if th_time.hour >= 1:
            news_log = db.query(models.DailyUpdateLog).filter(
                models.DailyUpdateLog.update_type == 'news',
                models.DailyUpdateLog.update_date == today
            ).first()

            if not news_log:
                print("[Scheduler] Missed 'news' sync. Scheduling now...")
                scheduler.add_job(
                    update_news_daily,
                    'date',
                    run_date=datetime.now() + timedelta(seconds=5),
                    id='catchup_news',
                    name='Catch-up: News'
                )
                
        # 4. Check 'sentiment' update (Scheduled: 02:00 TH)
        if th_time.hour >= 2:
            sentiment_log = db.query(models.DailyUpdateLog).filter(
                models.DailyUpdateLog.update_type == 'sentiment',
                models.DailyUpdateLog.update_date == today
            ).first()
            
            if not sentiment_log:
                print("[Scheduler] Missed 'sentiment' update. Scheduling now (Force Update)...")
                scheduler.add_job(
                    update_all_sentiments, 
                    'date', 
                    run_date=datetime.now() + timedelta(seconds=10),
                    kwargs={'force_update': True}, 
                    id='catchup_sentiment', 
                    name='Catch-up: Sentiment'
                )

        # 5. Check 'tags' update (Scheduled: 03:00 TH)
        if th_time.hour >= 3:
            tags_log = db.query(models.DailyUpdateLog).filter(
                models.DailyUpdateLog.update_type == 'tags',
                models.DailyUpdateLog.update_date == today
            ).first()
            
            if not tags_log:
                print("[Scheduler] Missed 'tags' update. Scheduling now...")
                scheduler.add_job(
                    update_review_tags, 
                    'date', 
                    run_date=datetime.now() + timedelta(seconds=15),
                    kwargs={'update_existing': True}, 
                    id='catchup_tags', 
                    name='Catch-up: Review Tags'
                )

        # 6. Check 'reviews' (Thai reviews) (Scheduled: 04:00 TH)
        if th_time.hour >= 4:
            reviews_log = db.query(models.DailyUpdateLog).filter(
                models.DailyUpdateLog.update_type == 'reviews',
                models.DailyUpdateLog.update_date == today
            ).first()
            
            if not reviews_log:
                print("[Scheduler] Missed 'reviews' update. Scheduling now (Smart Update)...")
                scheduler.add_job(
                    update_thai_reviews_daily, 
                    'date', 
                    run_date=datetime.now() + timedelta(seconds=20),
                    id='catchup_reviews', 
                    name='Catch-up: Thai Reviews'
                )
            
    except Exception as e:
        print(f"[Scheduler] Error checking missed tasks: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    from datetime import timedelta # Ensure timedelta is available
    if not scheduler.running:
        scheduler.start()
        print("[Scheduler] Started - Thailand night schedule: Cleanup (00:05TH/17:05UTC), Games (00:10TH/17:10UTC), News (01:00TH/18UTC), Sentiment (02:00TH/19UTC), Tags (03:00TH/20UTC), Reviews (04:00TH/21UTC), Tokens (05:00TH/22UTC)")
        
        # Run catch-up check after 5 seconds
        scheduler.add_job(
            check_missed_daily_tasks, 
            'date', 
            run_date=datetime.now() + timedelta(seconds=5), 
            id='startup_check'
        )

def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Stopped")
