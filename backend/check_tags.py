import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Game

def check_tags():
    db = SessionLocal()
    try:
        madoka = db.query(Game).filter(Game.title.ilike('%madoka%')).first()
        dota = db.query(Game).filter(Game.title.ilike('%dota 2%')).first()
        
        if madoka:
            print(f"Game: {madoka.title}")
            print(f"Tags: {madoka.genre}")
        else:
            print("Madoka not found")
            
        print("-" * 20)
        
        if dota:
            print(f"Game: {dota.title}")
            print(f"Tags: {dota.genre}")
        else:
            print("Dota 2 not found")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_tags()
