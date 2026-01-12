import sys
import os

# Ensure we can import from app
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models import Review, Game
from app.database import DATABASE_URL
from collections import Counter



def main():
    print(f"Connecting to {DATABASE_URL}")
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
            
            steam_revs = [r for r in reviews if r.is_steam_review or r.steam_id]
            
            # Use the NEW validator
            from app.utils.thai_validator import is_valid_thai_content
            
            thai_passing = [r for r in steam_revs if is_valid_thai_content(r.content)]
            
            print(f"  - Total reviews in DB: {len(reviews)}")
            print(f"  - (NEW LOGIC) Valid Thai Reviews: {len(thai_passing)} (Total Steam: {len(steam_revs)})")
            
            # Test specific cases
            test_cases = [
                ("Pure English", "This is a good game."),
                ("Mixed", "Game นี้สนุกมาก very good"),
                ("Short Thai", "ดี"),
                ("Short Thai (Valid)", "สนุกมากๆ"),
                ("No Result", "")
            ]
            print("\n  [TESTING NEW VALIDATOR]")
            for name, text in test_cases:
                result = is_valid_thai_content(text)
                print(f"  - {name}: {'PASS' if result else 'FAIL'} (Text: {text})")

            
            if len(steam_revs) > 20:
                print("  [SUCCESS] Found significantly more reviews with the fix!")

                print("  [POTENTIAL ISSUE REPRODUCED]")
                print("  Sample filtered out reviews:")
                filtered_out = [r for r in steam_revs if not is_valid_thai_content(r.content)]
                for r in filtered_out[:3]:
                    content_preview = r.content[:100].replace('\n', ' ') if r.content else "Empty"
                    print(f"    - Content: {content_preview}...")
                    
                    if r.content:
                        thai_c = sum(1 for c in r.content if '\u0E00' <= c <= '\u0E7F')
                        total_c = len([c for c in r.content if c.isalpha()])
                        if total_c > 0:
                            print(f"      Ratio: {thai_c}/{total_c} = {thai_c/total_c:.4f}")
                        else:
                            print(f"      Ratio: 0 (total_chars=0)")
                    else:
                        print(f"      Ratio: 0 (Empty content)")
            
            # Check Playtime Data
            print("  [PLAYTIME CHECK]")
            playtime_data = [r.playtime_hours for r in thai_passing if r.playtime_hours is not None]
            has_playtime = len([p for p in playtime_data if p > 0])
            print(f"    - Reviews with Playtime > 0: {has_playtime}/{len(thai_passing)}")
            if len(playtime_data) > 0:
                print(f"    - Sample Playtimes: {playtime_data[:5]}")
            else:
                print("    - No playtime data found!")
        print("")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()
