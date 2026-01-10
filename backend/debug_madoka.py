import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.database import SessionLocal
from app.models import Game, Review as SteamReview
from app.utils.thai_validator import is_valid_thai_content

def debug_madoka():
    db = SessionLocal()
    try:
        # 1. Find the game
        print("Searching for 'Madoka'...")
        games = db.query(Game).filter(Game.title.ilike('%madoka%')).all()
        
        if not games:
            print("No game found with 'Madoka' in the title.")
            return

        for game in games:
            print(f"\nFound Game: {game.title} (ID: {game.id}, Steam AppID: {game.steam_app_id})")
            
            # 2. Get Raw Reviews
            reviews = db.query(SteamReview).filter(SteamReview.game_id == game.id).all()
            print(f"Total Raw Steam Reviews in DB: {len(reviews)}")
            
            if not reviews:
                print(" -> No reviews in database. Crawler might not have run or found 0 reviews.")
                continue

            # 3. Analyze each review
            print("-" * 50)
            print("Analyzing Reviews against Filter:")
            print("-" * 50)
            
            passed_count = 0
            for r in reviews:
                is_valid = is_valid_thai_content(r.content)
                status = "PASS" if is_valid else "FAIL"
                if is_valid:
                    passed_count += 1
                    
                # Print details for Fails (to understand why) and a few Passes
                if not is_valid or passed_count <= 3:
                     summary = r.content[:50].replace('\n', ' ') + "..." if len(r.content) > 50 else r.content.replace('\n', ' ')
                     print(f"[{status}] ID: {r.steam_id} | Content: {summary}")
            
            print("-" * 50)
            print(f"Summary: {passed_count}/{len(reviews)} reviews passed the Thai Validator.")
            print("-" * 50)

    finally:
        db.close()

if __name__ == "__main__":
    debug_madoka()
