from app.database import SessionLocal
from app import models
from sqlalchemy import text

def find_game():
    db = SessionLocal()
    try:
        # Search for the game
        games = db.query(models.Game).filter(models.Game.title.ilike('%Clair Obscur%')).all()
        for game in games:
            print(f"Found Game: {game.title} (ID: {game.id}, SteamID: {game.steam_app_id})")
    finally:
        db.close()

if __name__ == "__main__":
    find_game()
