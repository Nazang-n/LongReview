"""
Admin API routes
Handles administrative functions like manual updates
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict
from ..database import get_db
from ..scheduler import update_all_sentiments, update_review_tags

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/review-tags/update")
async def trigger_review_tags_update(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger review tag update for all games (admin endpoint)
    
    This will update review tags for games that:
    - Have no tags yet
    - Have tags older than 7 days
    
    Returns:
        Status message and statistics about the update
    """
    from ..scheduler import update_review_tags
    
    try:
        stats = update_review_tags()
        
        return {
            "status": "success",
            "message": f"Checked {stats['games_checked']} games: {stats['updated']} updated, {stats['skipped']} skipped",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update review tags: {str(e)}",
            "stats": {
                "games_checked": 0,
                "updated": 0,
                "skipped": 0,
                "errors": 0
            }
        }


@router.post("/sentiment/update")
async def trigger_sentiment_update(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger sentiment update for all games (admin endpoint)
    
    Returns:
        Status message and statistics about the update
    """
    from ..scheduler import update_all_sentiments
    
    try:
        stats = update_all_sentiments()
        
        return {
            "status": "success",
            "message": f"Updated {stats['updated']} games, {stats['errors']} errors",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update sentiments: {str(e)}",
            "stats": {
                "games_processed": 0,
                "updated": 0,
                "errors": 0
            }
        }


@router.post("/reviews/update")
async def trigger_thai_reviews_update(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger Thai review fetching for all games (admin endpoint)
    
    This will fetch Thai reviews from Steam for games that:
    - Have never been fetched
    - Haven't been updated in 24+ hours
    
    Reviews will be displayed in game detail pages under "รีวิวจาก Steam (ภาษาไทย)"
    
    Returns:
        Status message and statistics about the update
    """
    from ..services.review_scheduler import trigger_manual_update
    
    # Run synchronously to get stats (it's already fast enough)
    try:
        stats = trigger_manual_update()
        
        return {
            "status": "success",
            "message": f"Updated {stats['games_processed']} games: {stats['successful']} successful, {stats['failed']} failed",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update Thai reviews: {str(e)}",
            "stats": {
                "games_processed": 0,
                "successful": 0,
                "failed": 0,
                "total_new_reviews": 0
            }
        }


@router.get("/analytics/comments")
async def get_comment_analytics(db: Session = Depends(get_db)) -> Dict:
    """
    Get comment statistics for the current month
    Returns daily counts, today's count, and monthly total
    """
    from sqlalchemy import func, extract
    from datetime import datetime, timedelta
    from ..models import Comment
    
    try:
        now = datetime.now()
        first_day_of_month = datetime(now.year, now.month, 1)
        
        # Get daily counts for current month
        daily_stats = db.query(
            func.date(Comment.created_at).label('date'),
            func.count(Comment.id).label('count')
        ).filter(
            Comment.created_at >= first_day_of_month
        ).group_by(
            func.date(Comment.created_at)
        ).order_by(
            func.date(Comment.created_at)
        ).all()
        
        # Get today's count
        today_start = datetime(now.year, now.month, now.day)
        today_count = db.query(func.count(Comment.id)).filter(
            Comment.created_at >= today_start
        ).scalar() or 0
        
        # Get monthly total
        monthly_total = db.query(func.count(Comment.id)).filter(
            Comment.created_at >= first_day_of_month
        ).scalar() or 0
        
        return {
            "daily": [{"date": str(stat.date), "count": stat.count} for stat in daily_stats],
            "today_count": today_count,
            "monthly_total": monthly_total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comment analytics: {str(e)}")


@router.get("/analytics/news")
async def get_news_analytics(db: Session = Depends(get_db)) -> Dict:
    """
    Get news statistics for the current month
    Returns daily counts, today's count, and monthly total
    """
    from sqlalchemy import func
    from datetime import datetime
    from ..models import News
    
    try:
        now = datetime.now()
        first_day_of_month = datetime(now.year, now.month, 1)
        
        # Get daily counts for current month
        daily_stats = db.query(
            func.date(News.created_at).label('date'),
            func.count(News.id).label('count')
        ).filter(
            News.created_at >= first_day_of_month
        ).group_by(
            func.date(News.created_at)
        ).order_by(
            func.date(News.created_at)
        ).all()
        
        # Get today's count
        today_start = datetime(now.year, now.month, now.day)
        today_count = db.query(func.count(News.id)).filter(
            News.created_at >= today_start
        ).scalar() or 0
        
        # Get monthly total
        monthly_total = db.query(func.count(News.id)).filter(
            News.created_at >= first_day_of_month
        ).scalar() or 0
        
        return {
            "daily": [{"date": str(stat.date), "count": stat.count} for stat in daily_stats],
            "today_count": today_count,
            "monthly_total": monthly_total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news analytics: {str(e)}")


@router.get("/analytics/reports")
async def get_report_analytics(db: Session = Depends(get_db)) -> Dict:
    """
    Get comment report statistics for the current month (pending reports only)
    Returns daily counts, today's count, and monthly total of pending reports
    """
    from sqlalchemy import func
    from datetime import datetime
    from ..models import CommentReport
    
    try:
        now = datetime.now()
        first_day_of_month = datetime(now.year, now.month, 1)
        
        # Get daily counts for current month (pending only)
        daily_stats = db.query(
            func.date(CommentReport.created_at).label('date'),
            func.count(CommentReport.id).label('count')
        ).filter(
            CommentReport.created_at >= first_day_of_month,
            CommentReport.status == 'pending'
        ).group_by(
            func.date(CommentReport.created_at)
        ).order_by(
            func.date(CommentReport.created_at)
        ).all()
        
        # Get today's count (pending only)
        today_start = datetime(now.year, now.month, now.day)
        today_count = db.query(func.count(CommentReport.id)).filter(
            CommentReport.created_at >= today_start,
            CommentReport.status == 'pending'
        ).scalar() or 0
        
        # Get monthly total (pending only)
        monthly_total = db.query(func.count(CommentReport.id)).filter(
            CommentReport.created_at >= first_day_of_month,
            CommentReport.status == 'pending'
        ).scalar() or 0
        
        return {
            "daily": [{"date": str(stat.date), "count": stat.count} for stat in daily_stats],
            "today_count": today_count,
            "monthly_total": monthly_total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch report analytics: {str(e)}")
