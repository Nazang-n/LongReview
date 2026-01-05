"""
Migration script to add last_review_fetch column to game table (PostgreSQL)
Uses the same database connection as your app
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text

try:
    print("Adding last_review_fetch column to game table...")
    
    with engine.connect() as conn:
        # Add the column
        conn.execute(text("""
            ALTER TABLE game 
            ADD COLUMN last_review_fetch TIMESTAMP NULL
        """))
        conn.commit()
    
    print("SUCCESS: Added last_review_fetch column")
    print("\nMigration complete!")
    
except Exception as err:
    if "already exists" in str(err) or "duplicate column" in str(err).lower():
        print("WARNING: Column last_review_fetch already exists")
    else:
        print(f"ERROR: {err}")
        raise
