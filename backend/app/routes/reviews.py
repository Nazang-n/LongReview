from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import or_
from .. import models, schemas
from ..database import get_db
from ..utils.thai_validator import is_valid_thai_content

router = APIRouter(
    prefix="/api/reviews",
    tags=["reviews"]
)


@router.get("/", response_model=List[schemas.Review])
def get_reviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all reviews with pagination."""
    reviews = db.query(models.Review).offset(skip).limit(limit).all()
    return reviews


@router.get("/game/{game_id}", response_model=List[schemas.Review])
def get_reviews_by_game(
    game_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all reviews for a specific game."""
    reviews = db.query(models.Review).filter(
        models.Review.game_id == game_id
    ).offset(skip).limit(limit).all()
    return reviews


@router.get("/{review_id}", response_model=schemas.Review)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get a specific review by ID."""
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with id {review_id} not found"
        )
    return review


@router.post("/", response_model=schemas.Review, status_code=status.HTTP_201_CREATED)
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    """Create a new review."""
    db_review = models.Review(**review.model_dump())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@router.put("/{review_id}", response_model=schemas.Review)
def update_review(
    review_id: int,
    review: schemas.ReviewUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing review."""
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if db_review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with id {review_id} not found"
        )
    
    update_data = review.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_review, key, value)
    
    db.commit()
    db.refresh(db_review)
    return db_review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: Session = Depends(get_db)):
    """Delete a review."""
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if db_review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with id {review_id} not found"
        )
    
    db.delete(db_review)
    db.commit()
    return None


# Steam Reviews Endpoints




@router.get("/steam/{game_id}")
def get_steam_reviews(
    game_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get Steam reviews for a specific game from database.
    Filters to show only Thai reviews and sorts by helpfulness.
    """
    # Get all Thai Steam reviews for this game
    reviews = db.query(models.Review).filter(
        models.Review.game_id == game_id,
        or_(
            models.Review.is_steam_review == True,
            models.Review.steam_id.isnot(None)
        )
    ).all()
    
    # Filter to only Thai reviews and calculate helpfulness score
    thai_reviews = []
    for r in reviews:
        if is_valid_thai_content(r.content):
            # Helpfulness score: (votes * 2) + content length
            # This prioritizes upvoted reviews and longer detailed reviews
            helpfulness_score = (r.helpful_count * 2) + len(r.content or "")
            thai_reviews.append((r, helpfulness_score))
    
    # Sort by helpfulness score (highest first) and limit
    thai_reviews.sort(key=lambda x: x[1], reverse=True)
    thai_reviews = thai_reviews[:limit]
    
    return {
        "success": True,
        "count": len(thai_reviews),
        "reviews": [
            {
                "id": r.id,
                "steam_id": r.steam_id,
                "author": r.steam_author,
                "content": r.content,
                "voted_up": r.voted_up,
                "helpful_count": r.helpful_count,
                "playtime_hours": r.playtime_hours,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r, _ in thai_reviews
        ]
    }


@router.post("/sync-steam/{game_id}")
def sync_steam_reviews(
    game_id: int,
    max_reviews: int = 100,  # Increased from 20 to get more quality reviews
    db: Session = Depends(get_db)
):
    """
    Sync Steam reviews for a game. Fetches from Steam API if not in database.
    """
    from ..steam_api import SteamAPIClient
    from datetime import datetime
    from sqlalchemy import text, or_
    
    print(f"[DEBUG] sync_steam_reviews called for game_id={game_id}, max_reviews={max_reviews}")
    
    try:
        # Get game's steam_app_id using raw SQL
        result = db.execute(
            text("SELECT steam_app_id FROM game WHERE id = :game_id"),
            {"game_id": game_id}
        )
        game_row = result.fetchone()
        
        if not game_row or not game_row[0]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game {game_id} not found or has no steam_app_id"
            )
        
        steam_app_id = game_row[0]
        
        # Check if we already have Steam reviews for this game
        existing_reviews = db.query(models.Review).filter(
            models.Review.game_id == game_id,
            or_(
                models.Review.is_steam_review == True,
                models.Review.steam_id.isnot(None)
            )
        ).all()
        
        print(f"[DEBUG] Found {len(existing_reviews)} existing reviews in DB for game {game_id}")
        
        if existing_reviews:
            # Filter to only Thai reviews and sort by helpfulness
            thai_reviews = []
            for r in existing_reviews:
                if is_valid_thai_content(r.content):
                    thai_reviews.append(r)
            
            # Sort by helpfulness (votes_up)
            thai_reviews.sort(key=lambda r: r.helpful_count or 0, reverse=True)
            
            print(f"[DEBUG] After filtering: {len(thai_reviews)} Thai reviews found")
            
            # Return cached reviews
            return {
                "success": True,
                "cached": True,
                "count": len(thai_reviews),
                "reviews": [
                    {
                        "id": r.id,
                        "steam_id": r.steam_id,
                        "author": r.steam_author,
                        "content": r.content,
                        "voted_up": r.voted_up,
                        "helpful_count": r.helpful_count,
                        "playtime_hours": r.playtime_hours,
                        "created_at": r.created_at.isoformat() if r.created_at else None
                    }
                    for r in thai_reviews
                ]
            }
        
        # Fetch from Steam API
        # Fetch Thai reviews for display in the "Read Reviews" section
        steam_reviews = SteamAPIClient.get_all_reviews(
            app_id=int(steam_app_id),
            language="thai",
            max_reviews=max_reviews
        )
        
        
        if not steam_reviews:
            return {
                "success": True,
                "cached": False,
                "count": 0,
                "reviews": [],
                "message": "No Thai reviews found on Steam"
            }
        
        # Save reviews to database
        saved_reviews = []
        
        # Helper set to track what we've added in this transaction
        # This prevents "Duplicate entry" if Steam API returns the same review twice in the same batch
        processed_steam_ids = set()

        # Helper set to check against DB
        # Get all existing steam_ids for this game
        db_existing_ids = {
            r[0] for r in db.query(models.Review.steam_id).filter(
                models.Review.game_id == game_id,
                models.Review.steam_id.isnot(None)
            ).all()
        }
        
        for steam_review in steam_reviews:
            rec_id = steam_review.get("recommendationid")
            review_content = steam_review.get("review", "")
            
            # Skip if no ID or already exists in DB or already processed in this batch
            if not rec_id:
                print(f"[DEBUG] Skipping review: no rec_id")
                continue
            if rec_id in db_existing_ids:
                print(f"[DEBUG] Skipping review {rec_id}: already in DB")
                continue
            if rec_id in processed_steam_ids:
                print(f"[DEBUG] Skipping review {rec_id}: already processed in this batch")
                continue
            
            # Note: We're using Steam's language="thai" filter, so we trust that these are Thai reviews
            # No need for additional Thai content validation
                
            processed_steam_ids.add(rec_id)

            playtime_minutes = steam_review.get("author", {}).get("playtime_at_review", 0)
            playtime_hours = round(playtime_minutes / 60, 1) if playtime_minutes else 0
            
            timestamp = steam_review.get("timestamp_created")
            created_date = datetime.fromtimestamp(timestamp) if timestamp else None
            
            new_review = models.Review(
                game_id=game_id,
                owner=steam_review.get("author", {}).get("steamid", "Unknown"),
                content=review_content,
                steam_id=rec_id,
                is_steam_review=True,
                steam_author=steam_review.get("author", {}).get("steamid", "Unknown"),
                voted_up=steam_review.get("voted_up", True),
                helpful_count=steam_review.get("votes_up", 0),
                playtime_hours=playtime_hours,
                created_at=created_date
            )
            
            db.add(new_review)
            saved_reviews.append({
                "id": new_review.id,  # Note: ID won't be available until commit/flush if not using RETURNING
                "steam_id": new_review.steam_id,
                "author": new_review.steam_author,
                "content": new_review.content,
                "voted_up": new_review.voted_up,
                "helpful_count": new_review.helpful_count,
                "playtime_hours": new_review.playtime_hours,
                "created_at": new_review.created_at.isoformat() if new_review.created_at else None
            })
        
        if saved_reviews:
            db.commit()
            # Refresh to get IDs
            for review_data in saved_reviews:
                 # Re-querying is expensive, just return success. 
                 # Or we can do db.refresh(new_review) inside the loop if performance allows. 
                 # For batch logic, refreshing inside loop might be slow but safe.
                 pass
        else:
             # Nothing new saved
             pass
        
        # Sort saved reviews by helpfulness (votes_up) before returning
        sorted_reviews = sorted(saved_reviews, key=lambda r: r.get('helpful_count', 0), reverse=True)
        
        return {
            "success": True,
            "cached": False,
            "count": len(sorted_reviews),
            "reviews": sorted_reviews
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing Steam reviews: {str(e)}"
        )


@router.get("/sentiment/{game_id}")
def get_steam_sentiment(game_id: int, db: Session = Depends(get_db)):
    """Get sentiment from Steam reviews - stores only voted_up in analyreview table"""
    from ..steam_api import SteamAPIClient
    from sqlalchemy import text
    
    try:
        # Get steam_app_id
        result = db.execute(text("SELECT steam_app_id FROM game WHERE id = :game_id"), {"game_id": game_id})
        game_row = result.fetchone()
        if not game_row or not game_row[0]:
            # Game doesn't have steam_app_id, return empty result
            print(f"[Sentiment] Game {game_id} has no steam_app_id")
            return {
                "success": True,
                "total_reviews": 0,
                "positive_count": 0,
                "negative_count": 0,
                "positive_percent": 0,
                "negative_percent": 0,
                "cached": False
            }
        
        steam_app_id = int(game_row[0])
        
        # Use Steam API query_summary (Fast & Real-time)
        review_summary = SteamAPIClient.get_app_reviews(
            app_id=steam_app_id, 
            language="all", 
            num_per_page=0 # We only want summary, not actual reviews
        )
        
        if review_summary and review_summary.get("success") == 1:
            summary = review_summary.get("query_summary", {})
            total = summary.get("total_reviews", 0)
            positive = summary.get("total_positive", 0)
            negative = summary.get("total_negative", 0)
            
            # Calculate percentages
            if total > 0:
                pos_pct = round((positive / total * 100), 1)
                neg_pct = round((negative / total * 100), 1)
            else:
                pos_pct = 0
                neg_pct = 0
                
            return {
                "success": True,
                "total_reviews": total,
                "positive_count": positive,
                "negative_count": negative,
                "positive_percent": pos_pct,
                "negative_percent": neg_pct,
                "cached": False
            }
        
        # Fallback to empty result if API fails
        return {
            "success": False,
            "total_reviews": 0,
            "positive_count": 0,
            "negative_count": 0,
            "positive_percent": 0,
            "negative_percent": 0,
            "cached": False,
            "error": "Failed to fetch from Steam API"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Sentiment] Error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/sentiment/batch")
def get_batch_sentiment(game_ids: List[int], db: Session = Depends(get_db)):
    """Get sentiment from cached data in GameSentiment table"""
    if not game_ids:
        return {}
    
    results = {}
    
    try:
        # Get sentiment records from game_sentiment table
        sentiments = db.query(models.GameSentiment).filter(
            models.GameSentiment.game_id.in_(game_ids)
        ).all()
        
        for sentiment in sentiments:
            results[sentiment.game_id] = {
                "positive_percent": float(sentiment.positive_percent) if sentiment.positive_percent else 0,
                "negative_percent": float(sentiment.negative_percent) if sentiment.negative_percent else 0,
                "total_reviews": sentiment.total_reviews or 0,
                "review_score_desc": sentiment.review_score_desc or "No user reviews"
            }
                
    except Exception as e:
        print(f"[Batch Sentiment] Error: {e}")
    
    return results


@router.post("/sentiment/update-all")
def trigger_sentiment_update():
    """Manually trigger sentiment update for all games (Admin endpoint)"""
    from ..scheduler import update_all_sentiments
    
    # Run synchronously and return results
    result = update_all_sentiments()
    
    return {
        "success": True, 
        "message": "Sentiment update completed",
        "stats": result
    }



@router.post("/update-all-thai")
def update_all_thai_reviews(db: Session = Depends(get_db)):
    """
    Admin endpoint: Fetch new Thai reviews for all games (skip duplicates)
    """
    from sqlalchemy import text
    from ..steam_api import SteamAPIClient
    
    # Get all games with steam_app_id
    result = db.execute(text("SELECT id, steam_app_id, name FROM game WHERE steam_app_id IS NOT NULL"))
    games = result.fetchall()
    
    stats = {
        "games_processed": 0,
        "games_successful": 0,
        "games_failed": 0,
        "new_reviews_fetched": 0,
        "skipped_duplicates": 0,
        "errors": []
    }
    
    for game in games:
        game_id, steam_app_id, title = game
        stats["games_processed"] += 1
        
        try:
            # Fetch Thai reviews from Steam API
            steam_reviews = SteamAPIClient.get_all_reviews(
                app_id=int(steam_app_id),
                language="thai",
                max_reviews=100
            )
            
            if not steam_reviews:
                stats["games_failed"] += 1
                stats["errors"].append(f"{title}: No reviews returned from Steam")
                continue
            
            # Filter for Thai content and check for duplicates
            new_count = 0
            duplicate_count = 0
            
            for review in steam_reviews:
                steam_id = review.get("recommendationid")
                content = review.get("review", "")
                
                # Check if Thai content
                if not is_valid_thai_content(content):
                    continue
                
                # Check if already exists
                existing = db.query(models.Review).filter(
                    models.Review.steam_id == steam_id
                ).first()
                
                if existing:
                    duplicate_count += 1
                    continue
                
                # Save new review
                new_review = models.Review(
                    game_id=game_id,
                    steam_id=steam_id,
                    steam_author=review.get("author", {}).get("steamid"),
                    content=content,
                    voted_up=review.get("voted_up", True),
                    helpful_count=review.get("votes_up", 0),
                    playtime_hours=review.get("author", {}).get("playtime_forever", 0) / 60,
                    is_steam_review=True,
                    created_at=datetime.now()
                )
                db.add(new_review)
                new_count += 1
            
            db.commit()
            stats["games_successful"] += 1
            stats["new_reviews_fetched"] += new_count
            stats["skipped_duplicates"] += duplicate_count
            
            print(f"[DEBUG] Game {game_id}: {new_count} new, {duplicate_count} duplicates")
                
        except Exception as e:
            stats["games_failed"] += 1
            stats["errors"].append(f"{title}: {str(e)}")
            db.rollback()
    
    return {
        "success": True,
        "message": "Thai review update completed",
        "stats": stats
    }
