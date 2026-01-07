from app.database import SessionLocal
from app.models import Game, Review
from sqlalchemy import func

def check_ids():
    db = SessionLocal()
    try:
        print("--- Checking Games ---")
        games_count = db.query(Game).count()
        games_with_appid = db.query(Game).filter(Game.steam_app_id.isnot(None)).count()
        print(f"Total games: {games_count}")
        print(f"Games with steam_app_id: {games_with_appid}")
        
        if games_with_appid < games_count:
            print("WARNING: Some games are missing steam_app_id!")
            missing = db.query(Game).filter(Game.steam_app_id.is_(None)).limit(5).all()
            for g in missing:
                print(f"  - Missing: {g.title} (ID: {g.id})")
        else:
            print("✅ All games have steam_app_id.")

        print("\n--- Checking Reviews ---")
        reviews_count = db.query(Review).count()
        reviews_with_steamid = db.query(Review).filter(Review.steam_id.isnot(None)).count()
        print(f"Total reviews: {reviews_count}")
        print(f"Reviews with steam_id: {reviews_with_steamid}")
        
        if reviews_with_steamid < reviews_count:
            print("WARNING: Some reviews are missing steam_id!")
            # Check if they are manual reviews or steam reviews
            steam_reviews_missing_id = db.query(Review).filter(
                Review.is_steam_review == True,
                Review.steam_id.is_(None)
            ).count()
            print(f"Steam reviews missing steam_id: {steam_reviews_missing_id}")

    finally:
        db.close()

if __name__ == "__main__":
    check_ids()
