import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models import Review, Game
from app.database import DATABASE_URL
from collections import Counter

# Copying the function from backend/app/routes/reviews.py
def is_thai_review(text: str, min_thai_ratio: float = 0.1) -> bool:
    if not text:
        return False
    
    # Count Thai characters (Unicode range 0E00-0E7F)
    thai_chars = sum(1 for c in text if '\u0E00' <= c <= '\u0E7F')
    # Count total alphabetic characters
    total_chars = len([c for c in text if c.isalpha()])
    
    if total_chars == 0:
        return False
    
    # Require at least 10% Thai characters
    return (thai_chars / total_chars) >= min_thai_ratio

def main():
    # Fix import issue by setting up path correctly relative to script location
    # Assuming script is in d:\LongReviewV2\LongReview\
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("--- Database Review Analysis ---")
    
    try:
        total_reviews = session.query(Review).count()
        steam_reviews = session.query(Review).filter(Review.is_steam_review == True).count()
        print(f"Total Reviews: {total_reviews}")
        print(f"Steam Reviews: {steam_reviews}")

        # Find game with most reviews
        most_reviewed = session.query(Review.game_id, func.count(Review.id))\
            .group_by(Review.game_id)\
            .order_by(func.count(Review.id).desc())\
            .limit(5).all()

        print("\nTop 5 Games by Review Count:")
        for game_id, count in most_reviewed:
            game = session.query(Game).filter(Game.id == game_id).first()
            title = game.title if game else "Unknown"
            print(f"Game ID: {game_id} ({title}) - {count} reviews")

            # Analyze this game's reviews
            reviews = session.query(Review).filter(Review.game_id == game_id).all()
            
            steam_revs = [r for r in reviews if r.is_steam_review]
            thai_passing = [r for r in steam_revs if is_thai_review(r.content)]
            
            print(f"  - Total reviews in DB: {len(reviews)}")
            print(f"  - is_steam_review=True: {len(steam_revs)}")
            print(f"  - Passing is_thai_review: {len(thai_passing)}")
            
            if len(steam_revs) > 0 and len(thai_passing) <= 1:
                print("  [POTENTIAL ISSUE REPRODUCED]")
                print("  Sample filtered out reviews:")
                filtered_out = [r for r in steam_revs if not is_thai_review(r.content)]
                for r in filtered_out[:3]:
                    print(f"    - Content: {r.content[:100]}...")
                    thai_c = sum(1 for c in r.content if '\u0E00' <= c <= '\u0E7F')
                    total_c = len([c for c in r.content if c.isalpha()])
                    if total_c > 0:
                        print(f"      Ratio: {thai_c}/{total_c} = {thai_c/total_c:.4f}")
                    else:
                        print(f"      Ratio: 0 (total_chars=0)")
            print("")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
