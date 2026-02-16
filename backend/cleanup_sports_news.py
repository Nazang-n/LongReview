"""
Quick script to delete sports news from database
Run this once to clean up existing sports news
"""
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import News
from app.config.settings import settings

# Create database session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Sports keywords to search for in titles
    sports_keywords = [
        "แข้ง", "ปีศาจแดง", "แม็กไกวร์", "ช้างศึก", "บัตรเชียร์",
        "ต่อสัญญา", "นักเตะ", "ทีมชาติ", "เติร์กเมนิสถาน",
        "กุนซือ", "แมนยู", "ฟุตบอล", "นัดชิง"
    ]
    
    # Find all news containing sports keywords
    sports_news = []
    for keyword in sports_keywords:
        news_items = db.query(News).filter(
            or_(
                News.title.ilike(f"%{keyword}%"),
                News.description.ilike(f"%{keyword}%")
            )
        ).all()
        sports_news.extend(news_items)
    
    # Remove duplicates
    sports_news = list(set(sports_news))
    
    print(f"Found {len(sports_news)} sports news articles")
    
    if sports_news:
        print("\nSports news to be deleted:")
        for news in sports_news[:10]:  # Show first 10
            try:
                print(f"- {news.title}")
            except:
                print(f"- [Title with special characters]")
        
        if len(sports_news) > 10:
            print(f"... and {len(sports_news) - 10} more")
        
        # Delete them
        for news in sports_news:
            db.delete(news)
        
        db.commit()
        print(f"\nDeleted {len(sports_news)} sports news articles!")
    else:
        print("No sports news found in database")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
