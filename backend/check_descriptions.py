"""Check actual news descriptions in database"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import News

db = SessionLocal()

try:
    # Get first 3 news articles
    news_items = db.query(News).filter(News.is_active == True).order_by(News.pub_date.desc()).limit(3).all()
    
    
    with open('description_check_results.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CHECKING NEWS DESCRIPTIONS IN DATABASE\n")
        f.write("=" * 80 + "\n")
        
        for i, item in enumerate(news_items, 1):
            f.write(f"\n{'='*80}\n")
            f.write(f"Article {i}: ID={item.article_id}\n")
            f.write(f"Title: {item.title}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Description length: {len(item.description) if item.description else 0} characters\n")
            f.write(f"\nFull description:\n")
            f.write(item.description if item.description else "None")
            f.write(f"\n\n{'='*80}\n")
            
            # Check for [...] in description
            if item.description and "[...]" in item.description:
                f.write("WARNING: Found [...] in description!\n")
            
            # Check for text after ...
            if item.description and "..." in item.description:
                parts = item.description.split("...")
                if len(parts) > 1:
                    after_ellipsis = parts[1].strip()
                    if after_ellipsis:
                        f.write(f"OK: Text after ... exists ({len(after_ellipsis)} chars)\n")
                        f.write(f"Sample: {after_ellipsis[:200]}\n")
                    else:
                        f.write("ERROR: No text after ...\n")
    
    print("Results written to description_check_results.txt")
    
finally:
    db.close()
