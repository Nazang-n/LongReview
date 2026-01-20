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
            return {
                "status": "success",
                "message": f"Successfully generated tags for game {game_id}",
                "data": result,
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
        # Query games that don't have any review tags
        # We check for NOT EXISTS in game_review_tags
        untagged_games = db.query(Game).filter(
            ~exists().where(GameReviewTag.game_id == Game.id),
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
    Manually trigger review tag update for all games (admin endpoint)
    
    This will update review tags for games that:
    - Have no tags yet (MISSING TAGS ONLY)
    
    Returns:
        Status message and statistics about the update
    """
    from ..scheduler import update_review_tags
    
    try:
        # Pass True to Check expiry of existing tags
        stats = update_review_tags(update_existing=True)
        
        return {
            "status": "success",
            "message": f"Checked {stats['games_checked']} games: {stats['updated']} updated (new), {stats['skipped']} skipped (already has tags)",
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


@router.post("/games/import-newest")
async def trigger_newest_games_import(background_tasks: BackgroundTasks) -> Dict:
    """
    Manually trigger import of newest games from Steam (admin endpoint)
    
    Returns:
        Status message and statistics about the import
    """
    from ..scheduler import import_newest_games
    
    try:
        stats = import_newest_games()
        
        return {
            "status": "success",
            "message": f"Imported {stats['imported']} games, {stats['skipped']} skipped, {stats['failed']} failed",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to import newest games: {str(e)}",
            "stats": {
                "imported": 0,
                "skipped": 0,
                "failed": 0
            }
        }


@router.post("/sentiment/update/{game_id}")
async def update_single_game_sentiment(game_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Update sentiment for a single game (does NOT log to daily_update_log)
    Used for individual game fixes from admin panel
    """
    from ..steam_api import SteamAPIClient
    from ..models import Game, GameSentiment
    from datetime import datetime
    
    try:
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game or not game.steam_app_id:
            return {
                "status": "error",
                "message": "Game not found or missing Steam App ID"
            }
        
        # Fetch sentiment from Steam
        sentiment_data = SteamAPIClient.get_review_summary(int(game.steam_app_id))
        
        if not sentiment_data:
            return {
                "status": "error",
                "message": "Failed to fetch sentiment data"
            }
        
        # Update or create sentiment
        sentiment = db.query(GameSentiment).filter(GameSentiment.game_id == game_id).first()
        
        if sentiment:
            sentiment.positive_percent = sentiment_data.get('positive_percent', 0)
            sentiment.negative_percent = sentiment_data.get('negative_percent', 0)
            sentiment.total_reviews = sentiment_data.get('total_reviews', 0)
            sentiment.review_score_desc = sentiment_data.get('review_score_desc', '')
            sentiment.last_updated = datetime.now()
        else:
            sentiment = GameSentiment(
                game_id=game_id,
                positive_percent=sentiment_data.get('positive_percent', 0),
                negative_percent=sentiment_data.get('negative_percent', 0),
                total_reviews=sentiment_data.get('total_reviews', 0),
                review_score_desc=sentiment_data.get('review_score_desc', ''),
                last_updated=datetime.now()
            )
            db.add(sentiment)
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Updated sentiment for {game.title}"
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


@router.get("/analytics/new-games-today")
async def get_new_games_today(db: Session = Depends(get_db)) -> Dict:
    """
    Get count of new games added today
    """
    from sqlalchemy import func
    from datetime import datetime
    from ..models import Game
    
    try:
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        
        # Count games created today (assuming Game has a created_at or similar field)
        # Since Game model doesn't have created_at, we'll use the daily_update_log
        from ..models import DailyUpdateLog
        
        # Get today's game import logs
        today_logs = db.query(DailyUpdateLog).filter(
            DailyUpdateLog.update_type == 'games',
            DailyUpdateLog.update_date == today_start.date()
        ).all()
        
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
    from datetime import datetime
    from ..models import DailyUpdateLog
    
    try:
        now = datetime.now()
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
    from datetime import date
    
    try:
        not_updated_games = []
        today = date.today()
        
        # Get all games with steam_app_id
        games = db.query(Game).filter(
            Game.steam_app_id.isnot(None)
        ).all()
        
        for game in games:
            not_updated = []
            
            # 1. Check if sentiment was updated today
            sentiment = db.query(GameSentiment).filter(
                GameSentiment.game_id == game.id
            ).first()
            
            if sentiment:
                if sentiment.last_updated:
                    last_update_date = sentiment.last_updated.date()
                    if last_update_date < today:
                        not_updated.append('sentiment')
                else:
                    not_updated.append('sentiment')
            else:
                # No sentiment data at all, needs update
                not_updated.append('sentiment')
            
            # 2. Check if tags are up-to-date (tags are valid for 7 days)
            tags = db.query(GameReviewTag).filter(
                GameReviewTag.game_id == game.id
            ).first()
            
            if tags:
                if tags.updated_at:
                    last_update_date = tags.updated_at.date()
                    # Calculate age of tags
                    days_diff = (today - last_update_date).days
                    if days_diff > 7:
                        not_updated.append('tags')
                else:
                    not_updated.append('tags')
            else:
                # No tags data at all, needs update
                not_updated.append('tags')
            
            # 3. Check if Thai reviews were fetched today
            if game.last_review_fetch:
                last_fetch_date = game.last_review_fetch.date()
                if last_fetch_date < today:
                    not_updated.append('reviews')
            else:
                # Never fetched reviews, needs update
                not_updated.append('reviews')
            
            # If any data was not updated today, add to list
            if not_updated:
                not_updated_games.append({
                    'id': game.id,
                    'title': game.title,
                    'steam_app_id': game.steam_app_id,
                    'not_updated': not_updated,  # What needs updating today
                    'last_sentiment_update': sentiment.last_updated.isoformat() if sentiment and sentiment.last_updated else None,
                    'last_tags_update': tags.updated_at.isoformat() if tags and tags.updated_at else None,
                    'last_review_fetch': game.last_review_fetch.isoformat() if game.last_review_fetch else None
                })
        
        return {
            "total_not_updated": len(not_updated_games),
            "games": not_updated_games
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch not updated games: {str(e)}")



