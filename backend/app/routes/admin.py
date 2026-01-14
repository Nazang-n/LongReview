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


@router.get("/games/list")
async def get_games_list(db: Session = Depends(get_db)) -> Dict:
    """
    Get list of all games (id and title) for admin dropdown
    """
    from ..models import Game
    
    try:
        games = db.query(Game.id, Game.title).order_by(Game.title).all()
        return {
            "games": [{"id": game.id, "title": game.title} for game in games]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch games list: {str(e)}")


@router.delete("/games/{game_id}")
async def delete_game(game_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Delete a game and all related data from the database
    
    This will delete:
    - Game sentiment data
    - Review tags
    - Steam reviews
    - Favorites
    - Comments (and comment reports)
    - The game itself
    """
    from ..models import Game, GameSentiment, Review, Favorite, Comment, CommentReport
    from sqlalchemy import text
    
    try:
        # Get game info before deletion
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        game_title = game.title
        
        # Delete related data in order (to respect foreign key constraints)
        # 1. Delete comment reports first
        comment_ids = db.query(Comment.id).filter(Comment.game_id == game_id).all()
        comment_ids = [c.id for c in comment_ids]
        if comment_ids:
            db.query(CommentReport).filter(CommentReport.comment_id.in_(comment_ids)).delete(synchronize_session=False)
        
        # 2. Delete comments
        comments_deleted = db.query(Comment).filter(Comment.game_id == game_id).delete(synchronize_session=False)
        
        # 3. Delete favorites
        favorites_deleted = db.query(Favorite).filter(Favorite.game_id == game_id).delete(synchronize_session=False)
        
        # 4. Delete reviews
        reviews_deleted = db.query(Review).filter(Review.game_id == game_id).delete(synchronize_session=False)
        
        # 5. Delete review tags (using parameterized query to prevent SQL injection)
        db.execute(text("DELETE FROM game_review_tags WHERE game_id = :game_id"), {"game_id": game_id})
        
        # 6. Delete game sentiment
        sentiment_deleted = db.query(GameSentiment).filter(GameSentiment.game_id == game_id).delete(synchronize_session=False)
        
        # 7. Finally delete the game
        db.delete(game)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Successfully deleted game: {game_title}",
            "deleted": {
                "game": game_title,
                "comments": comments_deleted,
                "favorites": favorites_deleted,
                "reviews": reviews_deleted,
                "sentiment": sentiment_deleted
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete game: {str(e)}")


