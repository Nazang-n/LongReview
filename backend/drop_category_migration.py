"""Drop category column from news table"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal, engine
from sqlalchemy import text

def drop_category_column():
    """Drop the category column from news table"""
    db = SessionLocal()
    try:
        # Drop the category column
        db.execute(text("ALTER TABLE news DROP COLUMN IF EXISTS category"))
        db.commit()
        print("✓ Successfully dropped category column from news table")
    except Exception as e:
        db.rollback()
        print(f"✗ Error dropping category column: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Dropping category column from news table...")
    drop_category_column()
