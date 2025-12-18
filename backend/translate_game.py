"""
Manually trigger translation for a specific game
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.translator import translator

load_dotenv()

def translate_game(game_id: int):
    """Manually translate a game's description to Thai"""
    try:
        database_url = os.getenv("DATABASE_URL")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Get game
            result = conn.execute(
                text("SELECT id, name, info, about_game_th FROM game WHERE id = :id"),
                {"id": game_id}
            )
            game = result.fetchone()
            
            if not game:
                print(f"Game {game_id} not found")
                return
            
            game_id, name, description, about_game_th = game
            
            print(f"\nGame: {name} (ID: {game_id})")
            print(f"Description: {description[:100]}..." if description else "No description")
            print(f"Current Thai: {about_game_th[:100]}..." if about_game_th else "No Thai content")
            
            if not description:
                print("\nNo description to translate!")
                return
            
            if about_game_th:
                print("\nThai content already exists. Skipping...")
                return
            
            # Translate
            print("\nTranslating to Thai...")
            thai_translation = translator.translate_to_thai(description)
            
            if thai_translation and thai_translation != description:
                # Save to database
                conn.execute(
                    text("UPDATE game SET about_game_th = :thai WHERE id = :id"),
                    {"thai": thai_translation, "id": game_id}
                )
                conn.commit()
                print("\nSUCCESS: Translation saved!")
                print(f"Thai: {thai_translation[:200]}...")
            else:
                print("\nERROR: Translation failed or returned same text")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # New World: Aeternum
    game_id = 637
    
    if len(sys.argv) > 1:
        game_id = int(sys.argv[1])
    
    print(f"Translating game ID: {game_id}")
    translate_game(game_id)
