"""
Migration script to add created_at column to game table
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get database URL from environment
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "longreview")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def add_created_at_to_game():
    """Add created_at column to game table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = 'game'
            AND COLUMN_NAME = 'created_at'
        """), {"db_name": DB_NAME})
        
        exists = result.fetchone()[0] > 0
        
        if exists:
            print("✓ Column 'created_at' already exists in 'game' table")
            return
        
        # Add the column
        print("Adding 'created_at' column to 'game' table...")
        conn.execute(text("""
            ALTER TABLE game
            ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        """))
        conn.commit()
        print("✓ Successfully added 'created_at' column to 'game' table")

if __name__ == "__main__":
    try:
        add_created_at_to_game()
        print("\n✓ Migration completed successfully!")
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        raise
