"""
Game Synchronization Service
Handles background tasks for syncing games from Steam API
"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
import requests
import random
import time

from app.database import SessionLocal
from app import models
from app.steam_api import SteamAPIClient
from app.routes import steam as steam_routes 

# Configure logging
logger = logging.getLogger(__name__)

class GameSyncService:
    """Service to handle background game synchronization"""
    
    _scheduler = None
    _is_running = False
    
    @classmethod
    def start_scheduler(cls):
        """Start the background scheduler"""
        if cls._scheduler and cls._scheduler.running:
            return
            
        cls._scheduler = AsyncIOScheduler()
        
        # Add sync job - run every 1 hour, start immediately
        cls._scheduler.add_job(
            cls.sync_games_job,
            IntervalTrigger(hours=1),
            id='sync_games',
            replace_existing=True,
            # next_run_time=datetime.now()
        )
        
        cls._scheduler.start()
        logger.info("Game sync scheduler started (Every 1 hour)")
        
    @classmethod
    def stop_scheduler(cls):
        """Stop the background scheduler"""
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown()
            logger.info("Game sync scheduler stopped")

    @classmethod
    async def sync_games_job(cls):
        """Background job to sync games"""
        if cls._is_running:
            logger.info("Game sync job already running, skipping...")
            return

        logger.info("Starting scheduled game sync")
        cls._is_running = True
        db = SessionLocal()
        
        try:
            # 1. Fetch full app list from Steam
            # Note: This is a large list (10MB+), so we fetch it once per cycle or cache it?
            # For simplicity, we fetch it fresh each time to get latest games, 
            # or we can use the "newest" logic if we trust it, but user wants "ALL" games.
            # actually fetching 50k items every hour might be heavy. 
            # Optimization: We could check if we have enough "candidate" games in a queue DB table?
            # But the requirement is simple: import games.
            
            # Let's import a batch of 20 new games (approx 500/day).
            await cls.import_new_games_batch(db, limit=20)
            
            logger.info("Scheduled game sync completed successfully")
            
        except Exception as e:
            logger.error(f"Scheduled game sync failed: {str(e)}")
        finally:
            cls._is_running = False
            db.close()

    @classmethod
    async def import_new_games_batch(cls, db: Session, limit: int = 100):
        """
        Fetch full game list, find games we don't have, and import a batch of them.
        """
        try:
            logger.info("Fetching complete app list from Steam...")
            # We need to implement this method in SteamAPIClient first
            all_apps = SteamAPIClient.get_all_games_list() # This returns [{'appid': 123, 'name': '...'}, ...]
            
            if not all_apps:
                logger.error("Failed to fetch app list from Steam")
                return

            logger.info(f"Got {len(all_apps)} apps from Steam. Filtering for new ones...")
            
            # Get multiple random chunks or iterate safely?
            # Random sampling is better to avoid getting stuck on broken IDs at the start of the list forever
            # But systematic is better for coverage. 
            # Let's shuffle the list to distribute imports across IDs? 
            # Or just filter efficiently.
            
            # Get Set of existing App IDs
            existing_app_ids = set(
                flat_id for (flat_id,) in db.query(models.Game.steam_app_id).filter(models.Game.steam_app_id.isnot(None)).all()
            )
            
            # Filter for new apps
            # Filter out non-games if possible (the API has 'name' which helps, but we can't be sure)
            # The API include_games=true helps.
            
            new_candidates = [
                app for app in all_apps 
                if app.get('appid') and app.get('appid') not in existing_app_ids
                and app.get('name') # skip empty names
            ]
            
            logger.info(f"Found {len(new_candidates)} new potential games to import.")
            
            if not new_candidates:
                logger.info("No new games to import.")
                return

            # Take the first 'limit' candidates? 
            # Or shuffle? Shuffling is fun but maybe we want latest?
            # Steam list is usually sorted by ID. Higher ID = Newer, mostly.
            # Reversing the list might give us newer games first.
            new_candidates.sort(key=lambda x: x['appid'], reverse=True) 
            
            batch_to_import = new_candidates[:limit]
            
            imported_count = 0
            
            for app in batch_to_import:
                app_id = app['appid']
                name = app['name']
                
                try:
                    logger.info(f"Importing {name} ({app_id})...")
                    
                    # Call our existing logic via direct function call if possible, 
                    # or replicate it. Replicating is safer for custom batch behavior.
                    
                    # Reuse the robust logic we just fixed in steam.py routes via internal call?
                    # Or duplicate minimal logic here?
                    # Let's use the SteamAPIClient + Models directly to avoid HTTP overhead/dependencies.
                    
                    success = await cls._import_single_game_internal(db, app_id)
                    if success:
                        imported_count += 1
                        
                    # Sleep to respect rate limits (100 games * 1.5s = 150s = 2.5 mins)
                    time.sleep(1.5) 
                    
                except Exception as e:
                    logger.error(f"Error importing {app_id}: {e}")
                    continue
                    
            logger.info(f"Batch finished. Imported {imported_count}/{limit} games.")
            
        except Exception as e:
            logger.error(f"Error in batch import: {e}")

    @staticmethod
    async def _import_single_game_internal(db: Session, app_id: int) -> bool:
        """Internal logic to import a single game, moved from routes or duplicated for service usage"""
        try:
             # Fetch app details from Steam (English for reliable metadata)
            app_details_en = SteamAPIClient.get_app_details(app_id, language="english", country_code="us")
            
            if not app_details_en:
                return False
                
            # Double check existence inside the loop (in case of race conditions or retries)
            existing = db.query(models.Game).filter(models.Game.steam_app_id == app_id).first()
            if existing:
                return False

            # Fetch Thai details
            app_details_th = SteamAPIClient.get_app_details(app_id, language="thai", country_code="th")
            
            # Imports locally to avoid circular deps at top level if any
            from app.utils.translator import translator
            from app.utils.text_cleaner import clean_html_text
            
            english_desc = None
            thai_desc = None
            
            if app_details_en.get('about_the_game'):
                english_desc = clean_html_text(app_details_en.get('about_the_game'))
            elif app_details_en.get('short_description'):
                english_desc = clean_html_text(app_details_en.get('short_description'))
                
            if app_details_th:
                about_th = app_details_th.get('about_the_game')
                if about_th:
                    cleaned_th = clean_html_text(about_th)
                    if translator.detect_language(cleaned_th) == 'th':
                        thai_desc = cleaned_th
            
            if not thai_desc and english_desc:
                try:
                    thai_desc = translator.translate_to_thai(english_desc)
                except:
                    pass
            
            # Parse Date
            release_date_obj = None
            rd = app_details_en.get('release_date', {})
            if rd.get('date') and not rd.get('coming_soon'):
                fmt_list = ['%d %b, %Y', '%b %d, %Y', '%Y-%m-%d']
                for fmt in fmt_list:
                    try:
                        release_date_obj = datetime.strptime(rd['date'], fmt).date()
                        break
                    except:
                        continue

            # Create Game
            new_game = models.Game(
                title=app_details_en.get("name"),
                description=english_desc,
                about_game_th=thai_desc,
                genre=", ".join([g["description"] for g in app_details_en.get("genres", [])[:3]]),
                image_url=app_details_en.get("header_image"),
                release_date=release_date_obj,
                developer=", ".join(app_details_en.get("developers", [])),
                publisher=", ".join(app_details_en.get("publishers", [])),
                steam_app_id=app_id
            )
            
            db.add(new_game)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to import game {app_id}: {e}")
            db.rollback()
            return False
