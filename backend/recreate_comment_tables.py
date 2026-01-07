"""
Recreate comment tables with correct structure
"""
from app.database import engine
from sqlalchemy import text

def recreate_comment_tables():
    """Drop and recreate all comment tables with correct structure"""
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Drop existing tables
            print("Dropping existing comment tables...")
            conn.execute(text("DROP TABLE IF EXISTS comment_report CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS comment_vote CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS comment CASCADE;"))
            
            # Create comment table with correct structure
            print("Creating comment table...")
            conn.execute(text("""
                CREATE TABLE comment (
                    id SERIAL PRIMARY KEY,
                    game_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    is_edited BOOLEAN DEFAULT FALSE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            conn.execute(text("CREATE INDEX idx_comment_game_id ON comment(game_id);"))
            conn.execute(text("CREATE INDEX idx_comment_user_id ON comment(user_id);"))
            
            # Create comment_vote table
            print("Creating comment_vote table...")
            conn.execute(text("""
                CREATE TABLE comment_vote (
                    id SERIAL PRIMARY KEY,
                    comment_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    vote_type VARCHAR(10) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (comment_id, user_id)
                );
            """))
            
            conn.execute(text("CREATE INDEX idx_comment_vote_comment_id ON comment_vote(comment_id);"))
            conn.execute(text("CREATE INDEX idx_comment_vote_user_id ON comment_vote(user_id);"))
            
            # Create comment_report table
            print("Creating comment_report table...")
            conn.execute(text("""
                CREATE TABLE comment_report (
                    id SERIAL PRIMARY KEY,
                    comment_id INTEGER NOT NULL,
                    reporter_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                    reviewed_by INTEGER,
                    reviewed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            conn.execute(text("CREATE INDEX idx_comment_report_comment_id ON comment_report(comment_id);"))
            conn.execute(text("CREATE INDEX idx_comment_report_status ON comment_report(status);"))
            
            trans.commit()
            print("SUCCESS: All comment tables recreated successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"ERROR: {e}")
            raise

if __name__ == "__main__":
    recreate_comment_tables()
