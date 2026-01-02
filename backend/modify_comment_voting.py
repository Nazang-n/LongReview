"""
Modify comment table to add upvotes column and drop comment_vote table
"""
from app.database import engine
from sqlalchemy import text

def modify_comment_tables():
    """Add upvotes to comment table and drop comment_vote table"""
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            print("Adding upvotes column to comment table...")
            conn.execute(text("""
                ALTER TABLE comment 
                ADD COLUMN IF NOT EXISTS upvotes INTEGER DEFAULT 0;
            """))
            
            print("Dropping comment_vote table...")
            conn.execute(text("DROP TABLE IF EXISTS comment_vote CASCADE;"))
            
            trans.commit()
            print("SUCCESS: Comment tables modified successfully!")
            print("- Added upvotes column to comment table")
            print("- Dropped comment_vote table")
            
        except Exception as e:
            trans.rollback()
            print(f"ERROR: {e}")
            raise

if __name__ == "__main__":
    modify_comment_tables()
