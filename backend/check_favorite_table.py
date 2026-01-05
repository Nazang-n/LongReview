"""
Check the actual structure of the favorite table in the database
"""
from app.database import engine
from sqlalchemy import text

def check_table_structure():
    """Check what columns exist in the favorite table"""
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'favorite'
            ORDER BY ordinal_position;
        """))
        
        print("Columns in 'favorite' table:")
        print("-" * 50)
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        print("-" * 50)

if __name__ == "__main__":
    check_table_structure()
