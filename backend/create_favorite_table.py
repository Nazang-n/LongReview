"""
Database migration script to create the favorite table.
Run this script to create the favorite table in your PostgreSQL database.
"""
from app.database import engine
from app.models import Base, Favorite

def create_favorite_table():
    """Create the favorite table"""
    print("Creating favorite table...")
    
    # Create only the favorite table
    Favorite.__table__.create(engine, checkfirst=True)
    
    print("✓ Favorite table created successfully!")

if __name__ == "__main__":
    create_favorite_table()
