"""
Test script to fetch Steam Thai reviews and save to database
"""
from app.database import get_db
from app import models
from app.steam_api import SteamAPIClient
from datetime import datetime
from sqlalchemy import text

def test_fetch_reviews(game_id: int):
    """Test fetching Steam reviews for a game"""
    db = next(get_db())
    
    try:
        # Get game using raw SQL to access steam_app_id
        result = db.execute(text("SELECT id, name, steam_app_id FROM game WHERE id = :game_id"), {"game_id": game_id})
        game_row = result.fetchone()
        
        if not game_row:
            print(f"[ERROR] Game {game_id} not found")
            return
        
        game_id_val, game_name, steam_app_id = game_row
        print(f"[OK] Found game: {game_name}")
        print(f"  Steam App ID: {steam_app_id}")
        
        if not steam_app_id:
            print(f"[ERROR] Game has no steam_app_id")
            return
        
        # Check existing reviews
        existing = db.query(models.Review).filter(
            models.Review.game_id == game_id,
            models.Review.is_steam_review == True
        ).count()
        print(f"  Existing Steam reviews: {existing}")
        
        if existing > 0:
            print("  Reviews already exist, showing first 3:")
            reviews = db.query(models.Review).filter(
                models.Review.game_id == game_id,
                models.Review.is_steam_review == True
            ).limit(3).all()
            for r in reviews:
                content_preview = r.content[:50] if len(r.content) > 50 else r.content
                print(f"    - {r.steam_author}: {content_preview}...")
            return
        
        # Fetch from Steam
        print(f"\n[FETCH] Fetching Thai reviews from Steam API (app_id: {steam_app_id})...")
        steam_reviews = SteamAPIClient.get_all_reviews(
            app_id=steam_app_id,
            language="thai",
            max_reviews=10
        )
        
        if not steam_reviews:
            print("[ERROR] No Thai reviews found")
            return
        
        print(f"[OK] Found {len(steam_reviews)} Thai reviews")
        
        # Save to database
        print(f"\n[SAVE] Saving reviews to database...")
        saved_count = 0
        for steam_review in steam_reviews:
            playtime_minutes = steam_review.get("author", {}).get("playtime_at_review", 0)
            playtime_hours = round(playtime_minutes / 60, 1) if playtime_minutes else 0
            
            timestamp = steam_review.get("timestamp_created")
            created_date = datetime.fromtimestamp(timestamp) if timestamp else None
            
            new_review = models.Review(
                game_id=game_id,
                admin_id=None,  # No admin for Steam reviews
                owner=steam_review.get("author", {}).get("steamid", "Unknown"),
                content=steam_review.get("review", ""),
                is_steam_review=True,
                steam_author=steam_review.get("author", {}).get("steamid", "Unknown"),
                voted_up=steam_review.get("voted_up", True),
                helpful_count=steam_review.get("votes_up", 0),
                playtime_hours=playtime_hours,
                created_at=created_date
            )
            
            db.add(new_review)
            saved_count += 1
            print(f"  [OK] Saved review from {new_review.steam_author}")
        
        db.commit()
        print(f"\n[SUCCESS] Successfully saved {saved_count} reviews!")
        print(f"\nNow visit http://localhost:4200/games/{game_id} to see the reviews!")
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # Test with game ID 727 (Left 4 Dead 2)
    print("=" * 60)
    print("Testing Steam Reviews Fetch")
    print("=" * 60)
    test_fetch_reviews(727)
