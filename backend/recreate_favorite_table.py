"""
Drop and recreate the favorite table with correct structure
"""
from app.database import engine
from sqlalchemy import text

def recreate_favorite_table():
    """Drop and recreate the favorite table"""
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Drop the table if it exists
            print("Dropping existing favorite table...")
            conn.execute(text("DROP TABLE IF EXISTS favorite CASCADE;"))
            
            # Create the table with correct structure
            print("Creating favorite table with correct structure...")
            conn.execute(text("""
                CREATE TABLE favorite (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    game_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (user_id, game_id)
                );
            """))
            
            # Create indexes
            print("Creating indexes...")
            conn.execute(text("CREATE INDEX idx_favorite_user_id ON favorite(user_id);"))
            conn.execute(text("CREATE INDEX idx_favorite_game_id ON favorite(game_id);"))
            
            # Commit transaction
            trans.commit()
            print("SUCCESS: Favorite table created successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"ERROR: {e}")
            raise

if __name__ == "__main__":
    recreate_favorite_table()
