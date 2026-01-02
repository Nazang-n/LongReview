"""
Check the actual structure of the comment table
"""
from app.database import engine
from sqlalchemy import text

def check_comment_table():
    """Check what columns exist in the comment table"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'comment'
            ORDER BY ordinal_position;
        """))
        
        print("Columns in 'comment' table:")
        print("-" * 50)
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        print("-" * 50)

if __name__ == "__main__":
    check_comment_table()
