"""
Manual Scheduler Trigger Script
Run this to execute all scheduler jobs immediately for testing
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scheduler import import_newest_games, update_all_sentiments, update_review_tags

async def run_all_scheduler_jobs():
    """Execute all scheduler jobs manually"""
    print("=" * 80)
    print("MANUAL SCHEDULER EXECUTION - ALL TASKS")
    print("=" * 80)
    print()
    
    # 1. Sync News
    print("[1/5] Running: Sync News")
    print("-" * 80)
    try:
        from app.database import SessionLocal
        from app.services.news_service import NewsService
        from app.models import DailyUpdateLog
        from datetime import date
        
        db = SessionLocal()
        result = await NewsService.sync_news_from_api(db, max_pages=6)
        
        # Log the update
        try:
            today = date.today()
            log_entry = DailyUpdateLog(
                update_type='news',
                update_date=today,
                status='success',
                items_processed=result.get('new_articles', 0) + result.get('updated_articles', 0),
                items_successful=result.get('new_articles', 0) + result.get('updated_articles', 0),
                items_failed=0
            )
            db.add(log_entry)
            db.commit()
            print("[LOG] News sync logged to daily_update_log")
        except Exception as e:
            print(f"[ERROR] Failed to log news sync: {e}")
            db.rollback()
        
        db.close()
        
        print(f"[SUCCESS] News Sync Complete:")
        print(f"  - Added: {result.get('new_articles', 0)}")
        print(f"  - Updated: {result.get('updated_articles', 0)}")
        print(f"  - Total Processed: {result.get('new_articles', 0) + result.get('updated_articles', 0)}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    print()
    
    # 2. Import newest games
    print("[2/5] Running: Import Newest Games")
    print("-" * 80)
    try:
        stats = import_newest_games()
        print(f"[SUCCESS] Import Newest Games Complete:")
        print(f"  - Imported: {stats.get('imported', 0)}")
        print(f"  - Skipped: {stats.get('skipped', 0)}")
        print(f"  - Failed: {stats.get('failed', 0)}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    print()
    
    # 3. Update all sentiments
    print("[3/5] Running: Update All Sentiments")
    print("-" * 80)
    try:
        stats = update_all_sentiments()
        print(f"[SUCCESS] Update Sentiments Complete:")
        print(f"  - Games Processed: {stats.get('games_processed', 0)}")
        print(f"  - Updated: {stats.get('updated', 0)}")
        print(f"  - Errors: {stats.get('errors', 0)}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    print()
    
    # 4. Update review tags
    print("[4/5] Running: Update Review Tags")
    print("-" * 80)
    try:
        stats = update_review_tags()
        print(f"[SUCCESS] Update Review Tags Complete:")
        print(f"  - Games Checked: {stats.get('games_checked', 0)}")
        print(f"  - Updated: {stats.get('updated', 0)}")
        print(f"  - Skipped: {stats.get('skipped', 0)}")
        print(f"  - Errors: {stats.get('errors', 0)}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    print()
    
    # 5. Update Thai reviews
    print("[5/5] Running: Update Thai Reviews")
    print("-" * 80)
    try:
        from app.services.review_scheduler import trigger_manual_update
        
        stats = trigger_manual_update()
        print(f"[SUCCESS] Update Thai Reviews Complete:")
        print(f"  - Games Processed: {stats.get('games_processed', 0)}")
        print(f"  - Successful: {stats.get('successful', 0)}")
        print(f"  - Failed: {stats.get('failed', 0)}")
        print(f"  - New Reviews: {stats.get('total_new_reviews', 0)}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    print()
    
    print("=" * 80)
    print("ALL SCHEDULER JOBS COMPLETED")
    print("=" * 80)
    print()
    print("Check your admin dashboard to see the updated status!")

if __name__ == "__main__":
    asyncio.run(run_all_scheduler_jobs())
