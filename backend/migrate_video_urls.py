"""
Migration script to fix video URLs for all games in the database.
This updates games to use the correct Steam API fields (hls_h264, dash_h264)
instead of the non-existent mp4/webm fields.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Game
from app.steam_api import SteamAPIClient
import json
import time

def update_game_videos():
    """Update video URLs for all games with steam_app_id"""
    db = SessionLocal()
    
    try:
        # Get all games that have a steam_app_id
        games = db.query(Game).filter(Game.steam_app_id.isnot(None)).all()
        
        total_games = len(games)
        print(f"Found {total_games} games with Steam App IDs")
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for index, game in enumerate(games, 1):
            try:
                print(f"\n[{index}/{total_games}] Processing: {game.title} (App ID: {game.steam_app_id})")
                
                # Fetch Steam API data
                steam_details = SteamAPIClient.get_app_details(
                    game.steam_app_id, 
                    language="english", 
                    country_code="us"
                )
                
                if not steam_details:
                    print(f"  [WARN] Could not fetch Steam data")
                    skipped_count += 1
                    continue
                
                # Extract videos with corrected fields
                movies = steam_details.get('movies', [])
                if not movies:
                    print(f"  [INFO] No videos available")
                    skipped_count += 1
                    continue
                
                videos_list = []
                for movie in movies:
                    videos_list.append({
                        "name": movie.get("name"),
                        "thumbnail": movie.get("thumbnail"),
                        "url": movie.get("dash_h264"),  # Corrected field
                        "hls_url": movie.get("hls_h264")  # Corrected field
                    })
                
                videos_json = json.dumps(videos_list)
                
                # Update the game's video field
                game.video = videos_json
                db.commit()
                
                print(f"  [OK] Updated with {len(videos_list)} video(s)")
                updated_count += 1
                
                # Be nice to Steam API - rate limit
                time.sleep(1.5)
                
            except Exception as e:
                print(f"  [ERROR] Error: {e}")
                error_count += 1
                db.rollback()
                continue
        
        print(f"\n" + "="*60)
        print(f"Migration Complete!")
        print(f"  [OK] Updated: {updated_count}")
        print(f"  [WARN] Skipped: {skipped_count}")
        print(f"  [ERROR] Errors: {error_count}")
        print(f"="*60)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("Video URL Migration Script")
    print("="*60)
    print("This will update video URLs for all games in the database.")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(0)
    
    update_game_videos()
