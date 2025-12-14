"""
Check database schema
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    # Parse connection string
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Get columns for user table
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'user'
    """)
    
    print("Columns in 'user' table:")
    for column in cursor.fetchall():
        print(f"  - {column[0]} ({column[1]})")
    
    cursor.close()
    conn.close()
    print("\nDone!")
    
except Exception as e:
    print(f"Error: {e}")
