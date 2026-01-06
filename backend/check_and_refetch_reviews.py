"""
Check review count for a specific game and re-fetch if needed
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.services.review_service import review_service
from sqlalchemy import text

def check_and_refetch_reviews(game_id: int):
    """
    Check current review count and re-fetch reviews
    
    Args:
        game_id: Game ID to check
    """
    db = SessionLocal()
    
    try:
        # Get game info
        result = db.execute(
            text("SELECT id, name, steam_app_id FROM game WHERE id = :game_id"),
            {"game_id": game_id}
        )
        game_row = result.fetchone()
        
        if not game_row:
            print(f"❌ Game {game_id} not found")
            return
        
        game_id, game_name, steam_app_id = game_row
        
        print(f"🎮 Game: {game_name}")
        print(f"   Steam App ID: {steam_app_id}")
        
        # Count current reviews
        result = db.execute(
            text("SELECT COUNT(*) FROM analyreview WHERE game_id = :game_id"),
            {"game_id": game_id}
        )
        current_count = result.fetchone()[0]
        
        print(f"   Current reviews in database: {current_count:,}")
        
        # Ask to re-fetch
        response = input("\n🔄 Re-fetch reviews? This will add new reviews (y/n): ")
        
        if response.lower() == 'y':
            print(f"\n📥 Fetching ALL reviews for {game_name}...")
            
            result = review_service.fetch_and_store_reviews(
                db=db,
                game_id=game_id,
                steam_app_id=steam_app_id
            )
            
            if result.get("success"):
                print(f"\n✅ Success!")
                print(f"   New reviews added: {result.get('new_reviews', 0):,}")
                print(f"   Total fetched from API: {result.get('total_fetched', 0):,}")
                
                # Count again
                result = db.execute(
                    text("SELECT COUNT(*) FROM analyreview WHERE game_id = :game_id"),
                    {"game_id": game_id}
                )
                new_count = result.fetchone()[0]
                print(f"   Total reviews in database now: {new_count:,}")
            else:
                print(f"\n❌ Failed: {result.get('error')}")
        else:
            print("Cancelled.")
        
    finally:
        db.close()


if __name__ == "__main__":
    game_id = int(input("Enter game_id: "))
    check_and_refetch_reviews(game_id)
