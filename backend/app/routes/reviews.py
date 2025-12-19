from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

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
    """Get Steam reviews for a specific game from database."""
    reviews = db.query(models.Review).filter(
        models.Review.game_id == game_id,
        models.Review.is_steam_review == True
    ).limit(limit).all()
    
    return {
        "success": True,
        "count": len(reviews),
        "reviews": [
            {
                "id": r.id,
                "author": r.steam_author,
                "content": r.content,
                "voted_up": r.voted_up,
                "helpful_count": r.helpful_count,
                "playtime_hours": r.playtime_hours,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reviews
        ]
    }


@router.post("/sync-steam/{game_id}")
def sync_steam_reviews(
    game_id: int,
    max_reviews: int = 20,
    db: Session = Depends(get_db)
):
    """
    Sync Steam reviews for a game. Fetches from Steam API if not in database.
    """
    from ..steam_api import SteamAPIClient
    from datetime import datetime
    from sqlalchemy import text
    
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
            models.Review.is_steam_review == True
        ).all()
        
        if existing_reviews:
            # Return cached reviews
            return {
                "success": True,
                "cached": True,
                "count": len(existing_reviews),
                "reviews": [
                    {
                        "id": r.id,
                        "author": r.steam_author,
                        "content": r.content,
                        "voted_up": r.voted_up,
                        "helpful_count": r.helpful_count,
                        "playtime_hours": r.playtime_hours,
                        "created_at": r.created_at.isoformat() if r.created_at else None
                    }
                    for r in existing_reviews
                ]
            }
        
        # Fetch from Steam API
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
        for steam_review in steam_reviews:
            playtime_minutes = steam_review.get("author", {}).get("playtime_at_review", 0)
            playtime_hours = round(playtime_minutes / 60, 1) if playtime_minutes else 0
            
            timestamp = steam_review.get("timestamp_created")
            created_date = datetime.fromtimestamp(timestamp) if timestamp else None
            
            new_review = models.Review(
                game_id=game_id,
                admin_id=None,
                owner=steam_review.get("author", {}).get("steamid", "Unknown"),
                content=steam_review.get("review", ""),
                is_steam_review=True,
                steam_author=steam_review.get("author", {}).get("steamid", "Unknown"),
                voted_up=steam_review.get("voted_up", True),
                helpful_count=steam_review.get("votes_up", 0),
                playtime_hours=playtime_hours,
                created_at=created_date
            )
            
            db.add(new_review)
            saved_reviews.append({
                "author": new_review.steam_author,
                "content": new_review.content,
                "voted_up": new_review.voted_up,
                "helpful_count": new_review.helpful_count,
                "playtime_hours": new_review.playtime_hours,
                "created_at": new_review.created_at.isoformat() if new_review.created_at else None
            })
        
        db.commit()
        
        return {
            "success": True,
            "cached": False,
            "count": len(saved_reviews),
            "reviews": saved_reviews
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing Steam reviews: {str(e)}"
        )
