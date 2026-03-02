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

@router.get("/tasks")
async def get_active_tasks() -> Dict:
    """Get all background tasks and their current status"""
    from ..services.task_manager import TaskManager
    return {"status": "success", "tasks": TaskManager.get_all_tasks()}

@router.delete("/tasks/{task_id}")
async def acknowledge_task(task_id: str) -> Dict:
    """Acknowledge a task to remove it from the active list"""
    from ..services.task_manager import TaskManager
    if TaskManager.remove_task(task_id):
        return {"status": "success", "message": "Task acknowledged and removed"}
    return {"status": "warning", "message": "Task not found"}



@router.post("/review-tags/generate/{game_id}")
async def generate_review_tags_for_game(game_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Manually trigger review tag generation for a specific game
    """
    from ..services.review_tags_service import ReviewTagsService
    
    try:
        service = ReviewTagsService(db)
        # Force generation regardless of age
        result = service.generate_tags_for_game(game_id, top_n=10, max_reviews=1500)
        
        if result.get('success'):
            # Get game name from database
            from ..models import Game
            game = db.query(Game).filter(Game.id == game_id).first()
            
            # Debug: Log what we found
            print(f"[DEBUG] Looking up game {game_id}")
            print(f"[DEBUG] Found game: {game}")
            print(f"[DEBUG] Game title: {game.title if game else 'None'}")
            
            game_name = game.title if game else f"Game {game_id}"
            
            print(f"[DEBUG] Final game_name: {game_name}")
            
            response_data = {
                **result,
                "game_name": game_name  # Add game name to response
            }
            
            print(f"[DEBUG] Response data keys: {response_data.keys()}")
            print(f"[DEBUG] game_name in response: {response_data.get('game_name')}")
            
            return {
                "status": "success",
                "message": f"Successfully generated tags for {game_name}",
                "data": response_data,
                "positive_tags": result.get('positive_tags', []),
                "negative_tags": result.get('negative_tags', [])
            }
        else:
            # Handle specific failures (e.g. No reviews)
            error_msg = result.get('error', 'Unknown error')
            status_code = "warning" if "No English reviews" in error_msg else "error"
            
            return {
                "status": status_code,
                "message": error_msg,
                "error": error_msg
            }
            
    except Exception as e:
        # Only catch genuine unexpected errors
        print(f"Error generating tags: {e}")
        return {
            "status": "error",
            "message": f"Internal Error: {str(e)}",
            "error": str(e)
        }

@router.get("/review-tags/missing")
async def get_missing_review_tags(db: Session = Depends(get_db)) -> Dict:
    """Get list of games that have NO review tags"""
    from ..models import Game, GameReviewTag
    from sqlalchemy import exists, not_
    
    try:
        # Query games that don't have any ACTUAL review tags (positive/negative)
        # Exclude system tags like 'no_reviews' or 'no_tags_generated'
        untagged_games = db.query(Game).filter(
            ~exists().where(
                (GameReviewTag.game_id == Game.id) &
                (GameReviewTag.tag_type.in_(['positive', 'negative']))
            ),
            Game.steam_app_id.isnot(None) # Only Steam games
        ).all()
        
        return {
            "success": True,
            "count": len(untagged_games),
            "games": [
                {
                    "id": g.id,
                    "title": g.title,
                    "steam_app_id": g.steam_app_id
                } for g in untagged_games
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch missing tags: {str(e)}")


@router.post("/review-tags/update")
async def trigger_review_tags_update(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger review tag update for all games (Background Task)
    """
    from ..scheduler import update_review_tags
    
    print("[Admin API] Review tags update endpoint called!")
    print("[Admin API] Adding background task to queue...")
    
    background_tasks.add_task(update_review_tags, update_existing=True)
    
    print("[Admin API] Background task added successfully")
    
    return {
        "status": "success",
        "message": "Review tags update started in background. Please check status in a few minutes.",
        "stats": {"status": "processing"}
    }


@router.post("/games/import-newest")
async def trigger_newest_games_import(limit: int = 10, db: Session = Depends(get_db)) -> Dict:
    """
    Manually trigger import of newest games from Steam (admin endpoint)
    Runs synchronously and returns actual import results.
    """
    from ..scheduler import import_newest_games
    
    # Cap limit at 10 for synchronous processing safety
    safe_limit = min(max(1, limit), 10)
    
    # Run synchronously so we get the actual results back
    stats = import_newest_games(target_limit=safe_limit)
    
    return {
        "status": "success",
        "message": f"Import complete. Added {stats.get('imported', 0)} new games.",
        "stats": {
            "added": stats.get("imported", 0),
            "skipped": stats.get("skipped", 0),
            "failed": stats.get("failed", 0),
            "imported_titles": stats.get("imported_titles", [])
        }
    }


@router.post("/sentiment/update/{game_id}")
async def update_single_game_sentiment(game_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Update sentiment for a single game (does NOT log to daily_update_log)
    Used for individual game fixes from admin panel
    """
    from ..models import Game
    from ..utils.sentiment_helper import fetch_and_cache_sentiment
    
    try:
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game or not game.steam_app_id:
            return {
                "status": "error",
                "message": "Game not found or missing Steam App ID"
            }
        
        # Use the helper function to fetch and cache sentiment
        success = fetch_and_cache_sentiment(game_id, int(game.steam_app_id), db)
        
        if success:
            return {
                "status": "success",
                "message": f"Updated sentiment for {game.title}"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to fetch sentiment data"
            }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Failed to update sentiment: {str(e)}"
        }


@router.post("/reviews/update/{game_id}")
async def update_single_game_reviews(game_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Update Thai reviews for a single game (does NOT log to daily_update_log)
    Used for individual game fixes from admin panel
    """
    from ..models import Game
    from ..utils.thai_review_helper import fetch_and_cache_thai_reviews
    
    try:
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game or not game.steam_app_id:
            return {
                "status": "error",
                "message": "Game not found or missing Steam App ID"
            }
        
        # Fetch Thai reviews
        success = fetch_and_cache_thai_reviews(game_id, game.steam_app_id, db, max_reviews=50)
        
        if success:
            return {
                "status": "success",
                "message": f"Updated Thai reviews for {game.title}"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to fetch Thai reviews"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update reviews: {str(e)}"
        }


@router.post("/sentiment/update")
async def trigger_sentiment_update(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger sentiment update for all games (Background Task)
    Uses Normal Update (only processes games not updated in the last 24h)
    """
    from ..scheduler import update_all_sentiments
    from ..services.task_manager import TaskManager
    
    task_id = TaskManager.create_task("วิเคราะห์เปอร์เซ็นรีวิว")
    
    def run_sentiment_with_task(tid: str):
        try:
            # Use normal update (force_update=False) to only process games not updated in the last 24h
            update_all_sentiments(force_update=False)
            TaskManager.update_task_success(tid, {"message": "วิเคราะห์เปอร์เซ็นต์รีวิวเสร็จสิ้น"})
        except Exception as e:
            TaskManager.update_task_error(tid, str(e))
            
    background_tasks.add_task(run_sentiment_with_task, task_id)
    
    return {
        "status": "success",
        "message": "Sentiment update started in background.",
        "stats": {"status": "processing", "task_id": task_id}
    }


@router.post("/reviews/update")
async def trigger_thai_reviews_update(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger Thai review fetching for all games (Background Task)
    Uses Normal Update (only processes games not fetched in the last 24h)
    """
    from ..services.review_scheduler import trigger_manual_update
    from ..services.task_manager import TaskManager
    
    task_id = TaskManager.create_task("ดึงรีวิวภาษาไทย")
    
    def run_reviews_with_task(tid: str):
        try:
            # Use normal update (force_update=False) to only process games not fetched in the last 24h
            trigger_manual_update(force_update=False)
            TaskManager.update_task_success(tid, {"message": "ดึงรีวิวภาษาไทยเสร็จสิ้น"})
        except Exception as e:
            TaskManager.update_task_error(tid, str(e))
            
    background_tasks.add_task(run_reviews_with_task, task_id)
    
    return {
        "status": "success",
        "message": "Thai reviews update started in background.",
        "stats": {"status": "processing", "task_id": task_id}
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
        now = datetime.utcnow() + timedelta(hours=7)
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
    from datetime import datetime, timedelta
    from ..models import News
    
    try:
        now = datetime.utcnow() + timedelta(hours=7)
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
    from datetime import datetime, timedelta
    from ..models import CommentReport
    
    try:
        now = datetime.utcnow() + timedelta(hours=7)
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


@router.get("/analytics/new-games-today")
async def get_new_games_today(db: Session = Depends(get_db)) -> Dict:
    """
    Get count of ALL new games added today (from any source: scheduler, manual import, etc.)
    """
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from ..models import Game
    
    try:
        now = datetime.utcnow() + timedelta(hours=7)
        today_start = datetime(now.year, now.month, now.day)
        
        # Count ALL games imported today via DailyUpdateLog
        # This includes: scheduler imports, manual admin imports, batch imports, etc.
        from ..models import DailyUpdateLog
        
        # Get all game import logs for today (not just scheduler)
        today_logs = db.query(DailyUpdateLog).filter(
            DailyUpdateLog.update_type.in_(['games', 'manual_game_import']),
            DailyUpdateLog.update_date == today_start.date()
        ).all()
        
        # Sum up successful imports from all sources
        total_new_games = sum(log.items_successful for log in today_logs)
        
        return {
            "date": str(today_start.date()),
            "new_games_count": total_new_games,
            "logs": [{
                "time": log.created_at.isoformat() if log.created_at else None,
                "count": log.items_successful,
                "status": log.status
            } for log in today_logs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch new games count: {str(e)}")


@router.get("/analytics/daily-updates")
async def get_daily_update_status(db: Session = Depends(get_db)) -> Dict:
    """
    Get today's update status for all data types (news, games, sentiment, tags, reviews)
    """
    from datetime import datetime, timedelta
    from ..models import DailyUpdateLog
    
    try:
        # Shift datetime by 7 hours so that UTC + 7 rolls over exactly at midnight TH
        now = datetime.utcnow() + timedelta(hours=7)
        today = now.date()
        
        # Get all update logs for today
        today_logs = db.query(DailyUpdateLog).filter(
            DailyUpdateLog.update_date == today
        ).all()
        
        # Organize by update type
        updates_by_type = {
            'news': {'fetched': False, 'status': 'not_run', 'count': 0, 'time': None},
            'games': {'fetched': False, 'status': 'not_run', 'count': 0, 'time': None},
            'sentiment': {'fetched': False, 'status': 'not_run', 'count': 0, 'time': None},
            'tags': {'fetched': False, 'status': 'not_run', 'count': 0, 'time': None},
            'reviews': {'fetched': False, 'status': 'not_run', 'count': 0, 'time': None}
        }
        
        for log in today_logs:
            update_type = log.update_type
            if update_type in updates_by_type:
                updates_by_type[update_type]['fetched'] = True
                updates_by_type[update_type]['status'] = log.status
                updates_by_type[update_type]['count'] = log.items_successful
                updates_by_type[update_type]['time'] = log.created_at.isoformat() if log.created_at else None
        
        return {
            "date": str(today),
            "updates": updates_by_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch daily update status: {str(e)}")




@router.get("/analytics/incomplete-games")
async def get_incomplete_games(db: Session = Depends(get_db)) -> Dict:
    """
    Get list of games that haven't been updated today
    
    A game is flagged if any of these were NOT updated today:
    - Sentiment data
    - Review tags  
    - Thai reviews
    """
    from ..models import Game, GameSentiment, GameReviewTag
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    try:
        not_updated_games = []
        today = (datetime.utcnow() + timedelta(hours=7)).date()
        
        # OPTIMIZED: Use a single query with joins instead of N+1 queries
        # This fetches all games with their sentiment and tags in ONE database hit
        games = db.query(Game).filter(
            Game.steam_app_id.isnot(None)
        ).outerjoin(
            GameSentiment, Game.id == GameSentiment.game_id
        ).add_columns(
            GameSentiment.last_updated.label('sentiment_updated'),
            GameSentiment.id.label('sentiment_id'),
            GameSentiment.tag_status.label('tag_status')
        ).all()
        
        # Pre-fetch all tag data in one query (much faster than per-game queries)
        tag_data = {}
        tag_query = db.query(
            GameReviewTag.game_id,
            func.max(GameReviewTag.updated_at).label('latest_tag_update'),
            func.count(GameReviewTag.id).label('tag_count')
        ).filter(
            GameReviewTag.tag_type.in_(['positive', 'negative'])
        ).group_by(GameReviewTag.game_id).all()
        
        for row in tag_query:
            tag_data[row.game_id] = {
                'updated_at': row.latest_tag_update,
                'count': row.tag_count
            }
        
        for game_row in games:
            game = game_row[0]  # The Game object
            sentiment_updated = game_row[1]  # sentiment.last_updated
            sentiment_id = game_row[2]  # sentiment.id
            tag_status = game_row[3]  # sentiment.tag_status

            not_updated = []

            # 1. Check if sentiment was updated today
            if sentiment_id:
                if sentiment_updated:
                    last_update_date = sentiment_updated.date()
                    if last_update_date < today:
                        not_updated.append('sentiment')
                else:
                    not_updated.append('sentiment')
            else:
                # No sentiment data at all
                not_updated.append('sentiment')

            # 2. Check if tags are up-to-date (tags are valid for 7 days)
            tags_info = tag_data.get(game.id)
            if tags_info and tags_info['count'] > 0:
                last_update_date = tags_info['updated_at'].date()
                days_diff = (today - last_update_date).days
                if days_diff > 7:
                    not_updated.append('tags')
            else:
                # No actual review tags
                not_updated.append('tags')

            # 3. Check if Thai reviews have ever been fetched.
            # The nightly scheduler re-fetches all games, so if a game has no Thai
            # reviews today, it may get them in the future. Only flag as incomplete
            # if we have NEVER attempted to fetch reviews for this game.
            if not game.last_review_fetch:
                not_updated.append('reviews')
            
            # If any data was not updated today, add to list
            if not_updated:
                not_updated_games.append({
                    'id': game.id,
                    'title': game.title,
                    'steam_app_id': game.steam_app_id,
                    'not_updated': not_updated,
                    'last_sentiment_update': sentiment_updated.isoformat() if sentiment_updated else None,
                    'last_tags_update': tags_info['updated_at'].isoformat() if tags_info and tags_info['updated_at'] else None,
                    'last_review_fetch': game.last_review_fetch.isoformat() if game.last_review_fetch else None,
                    'tag_status': tag_status
                })
        
        return {
            "total_not_updated": len(not_updated_games),
            "games": not_updated_games
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch not updated games: {str(e)}")


