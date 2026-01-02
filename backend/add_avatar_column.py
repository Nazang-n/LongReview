"""
Add avatar_url column to user table
"""
from app.database import engine
from sqlalchemy import text

def add_avatar_column():
    """Add avatar_url column to user table"""
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            print("Adding avatar_url column to user table...")
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS avatar_url TEXT;
            """))
            
            trans.commit()
            print("SUCCESS: avatar_url column added successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"ERROR: {e}")
            raise

if __name__ == "__main__":
    add_avatar_column()
