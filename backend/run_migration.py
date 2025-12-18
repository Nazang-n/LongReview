"""
Script to run SQL migration to add missing columns to game table
"""
import psycopg2
from app.database import SQLALCHEMY_DATABASE_URL

def run_migration():
    # Parse database URL
    # Format: postgresql://user:password@host:port/database
    db_url = SQLALCHEMY_DATABASE_URL.replace('postgresql://', '')
    
    try:
        # Read SQL file
        with open('migrations/add_game_columns.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(SQLALCHEMY_DATABASE_URL.replace('postgresql://', 'postgresql://'))
        cursor = conn.cursor()
        
        # Execute SQL script
        print("Running migration...")
        cursor.execute(sql_script)
        conn.commit()
        
        print("✅ Migration completed successfully!")
        
        # Show results
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'game' 
            ORDER BY ordinal_position;
        """)
        
        print("\n📋 Current columns in 'game' table:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}" + (f"({row[2]})" if row[2] else ""))
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        raise

if __name__ == "__main__":
    run_migration()
