"""
Test script to verify database connection and create tables
"""
from app.database import engine, Base
from app.models import User, Game, Review

try:
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    
    # Test connection
    with engine.connect() as connection:
        print("✓ Database connection successful!")
        print(f"✓ Connected to: {engine.url}")
        
    print("\nTables created:")
    print("  - user")
    print("  - games")
    print("  - reviews")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
