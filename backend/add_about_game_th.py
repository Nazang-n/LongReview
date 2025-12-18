"""
Migration script to add about_game_th column to game table
Run this script to add the Thai game details field to existing database
"""

from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_about_game_th_column():
    """Add about_game_th column to game table"""
    try:
        # Get database URL from environment (same as main app)
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            print("Error: DATABASE_URL not found in environment variables")
            return
        
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Check if column already exists
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('game')]
            
            if 'about_game_th' in columns:
                print("SUCCESS: Column 'about_game_th' already exists in 'game' table")
                return
            
            # Add the column (PostgreSQL syntax)
            connection.execute(text("""
                ALTER TABLE game 
                ADD COLUMN about_game_th TEXT NULL
            """))
            connection.commit()
            
            print("SUCCESS: Successfully added 'about_game_th' column to 'game' table")
            
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    print("Adding about_game_th column to game table...")
    add_about_game_th_column()


