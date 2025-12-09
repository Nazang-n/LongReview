from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..steam_api import SteamAPIClient

router = APIRouter(
    prefix="/api/steam",
    tags=["steam"]
)


@router.get("/reviews/{app_id}")
def fetch_steam_reviews(
    app_id: int,
    language: str = Query("thai", description="Language filter"),
    max_reviews: Optional[int] = Query(None, description="Maximum reviews to fetch"),
    db: Session = Depends(get_db)
):
    """
    Fetch reviews from Steam API for a specific app
    
    - **app_id**: Steam application ID (e.g., 570 for Dota 2)
    - **language**: Language filter (default: thai)
    - **max_reviews**: Maximum number of reviews to fetch (optional)
    """
    try:
        reviews = SteamAPIClient.get_all_reviews(
            app_id=app_id,
            language=language,
            max_reviews=max_reviews
        )
        
        return {
            "success": True,
            "app_id": app_id,
            "total_reviews": len(reviews),
            "reviews": reviews
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Steam reviews: {str(e)}"
        )


@router.get("/app/{app_id}")
def fetch_steam_app_details(app_id: int):
    """
    Fetch app details from Steam API
    
    - **app_id**: Steam application ID
    """
    try:
        app_details = SteamAPIClient.get_app_details(app_id)
        
        if not app_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"App {app_id} not found on Steam"
            )
        
        return {
            "success": True,
            "app_id": app_id,
            "data": app_details
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Steam app details: {str(e)}"
        )


@router.post("/import/game/{app_id}")
def import_game_from_steam(
    app_id: int,
    db: Session = Depends(get_db)
):
    """
    Import a game from Steam into the database
    
    - **app_id**: Steam application ID
    """
    try:
        # Fetch app details from Steam
        app_details = SteamAPIClient.get_app_details(app_id)
        
        if not app_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"App {app_id} not found on Steam"
            )
        
        # Check if game already exists
        existing_game = db.query(models.Game).filter(
            models.Game.title == app_details.get("name")
        ).first()
        
        if existing_game:
            return {
                "success": True,
                "message": "Game already exists",
                "game": existing_game
            }
        
        # Create new game
        new_game = models.Game(
            title=app_details.get("name"),
            description=app_details.get("short_description"),
            genre=", ".join([g["description"] for g in app_details.get("genres", [])[:3]]),
            image_url=app_details.get("header_image"),
            release_date=app_details.get("release_date", {}).get("date"),
            developer=", ".join(app_details.get("developers", [])),
            publisher=", ".join(app_details.get("publishers", []))
        )
        
        db.add(new_game)
        db.commit()
        db.refresh(new_game)
        
        return {
            "success": True,
            "message": "Game imported successfully",
            "game": new_game
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing game: {str(e)}"
        )


@router.post("/import/reviews/{app_id}")
def import_reviews_from_steam(
    app_id: int,
    game_id: int = Query(..., description="Game ID in your database"),
    user_id: int = Query(1, description="Default user ID for imported reviews"),
    language: str = Query("thai", description="Language filter"),
    max_reviews: int = Query(50, description="Maximum reviews to import"),
    db: Session = Depends(get_db)
):
    """
    Import reviews from Steam into the database
    
    - **app_id**: Steam application ID
    - **game_id**: Your database game ID
    - **user_id**: Default user ID for imported reviews
    - **language**: Language filter
    - **max_reviews**: Maximum number of reviews to import
    """
    try:
        # Fetch reviews from Steam
        steam_reviews = SteamAPIClient.get_all_reviews(
            app_id=app_id,
            language=language,
            max_reviews=max_reviews
        )
        
        imported_count = 0
        
        for steam_review in steam_reviews:
            # Create review in database
            new_review = models.Review(
                game_id=game_id,
                user_id=user_id,
                title=steam_review.get("review", "")[:255],  # Use first 255 chars as title
                content=steam_review.get("review", ""),
                rating=10 if steam_review.get("voted_up") else 5  # Convert to 0-10 scale
            )
            
            db.add(new_review)
            imported_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Imported {imported_count} reviews",
            "total_imported": imported_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing reviews: {str(e)}"
        )
