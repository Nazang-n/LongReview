from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import time
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


# ==================== SteamSpy API Endpoints ====================

@router.get("/steamspy/all")
def get_all_games_steamspy(
    limit: Optional[int] = Query(None, description="Limit number of games returned"),
    page: int = Query(0, description="Page number for pagination")
):
    """
    Fetch all games from SteamSpy API
    
    - **limit**: Limit number of games (optional, default: all)
    - **page**: Page number for pagination
    
    Returns dictionary with app_id as keys
    """
    try:
        games = SteamAPIClient.get_all_games_from_steamspy(page=page, limit=limit)
        
        if games is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch games from SteamSpy"
            )
        
        return {
            "success": True,
            "total_games": len(games),
            "games": games
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching SteamSpy data: {str(e)}"
        )


@router.get("/steamspy/top")
def get_top_games_steamspy(
    limit: int = Query(100, description="Number of top games to fetch", ge=1, le=1000)
):
    """
    Fetch top games by player count from SteamSpy
    
    - **limit**: Number of top games (1-1000, default: 100)
    
    Returns list of games sorted by popularity
    """
    try:
        games = SteamAPIClient.get_top_games_from_steamspy(limit=limit)
        
        if games is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch top games from SteamSpy"
            )
        
        return {
            "success": True,
            "total_games": len(games),
            "games": games
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching top games: {str(e)}"
        )


@router.get("/steamspy/game/{app_id}")
def get_game_details_steamspy(app_id: int):
    """
    Fetch game details from SteamSpy
    
    - **app_id**: Steam application ID
    
    Returns detailed game information from SteamSpy
    """
    try:
        game_details = SteamAPIClient.get_game_details_from_steamspy(app_id)
        
        if game_details is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game {app_id} not found on SteamSpy"
            )
        
        return {
            "success": True,
            "app_id": app_id,
            "data": game_details
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching game details: {str(e)}"
        )


@router.post("/steamspy/import/batch")
def import_games_batch_from_steamspy(
    limit: int = Query(50, description="Number of top games to import", ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Import top games from SteamSpy into the database
    
    - **limit**: Number of top games to import (1-500, default: 50)
    
    This will fetch top games from SteamSpy, then get detailed info from Steam API,
    and import them into your database
    """
    try:
        # Get top games from SteamSpy
        top_games = SteamAPIClient.get_top_games_from_steamspy(limit=limit)
        
        if not top_games:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch games from SteamSpy"
            )
        
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        
        for game in top_games:
            app_id = game.get('app_id')
            
            if not app_id:
                continue
            
            try:
                # Check if game already exists
                existing_game = db.query(models.Game).filter(
                    models.Game.title == game.get('name')
                ).first()
                
                if existing_game:
                    skipped_count += 1
                    continue
                
                # Fetch detailed info from Steam API (Thai language first)
                steam_details_th = SteamAPIClient.get_app_details(int(app_id), language="thai", country_code="th")
                
                if not steam_details_th:
                    # Try English as fallback
                    steam_details_th = SteamAPIClient.get_app_details(int(app_id), language="english", country_code="us")
                
                if not steam_details_th:
                    # Use SteamSpy data as fallback
                    new_game = models.Game(
                        title=game.get('name', 'Unknown'),
                        description=game.get('developer', ''),
                        genre=game.get('genre', ''),
                        image_url=None,
                        release_date=None,
                        developer=game.get('developer', ''),
                        publisher=game.get('publisher', ''),
                        platform=None,
                        price=None,
                        video=None
                    )
                else:
                    # Import translator
                    from ..utils.translator import translator
                    
                    # Get description (Thai or translated)
                    thai_desc = steam_details_th.get('short_description')
                    
                    # If description is in English, translate it
                    if thai_desc:
                        final_desc = translator.get_thai_description(thai_desc, thai_desc)
                    else:
                        final_desc = None
                    
                    # Extract platform info
                    platforms = steam_details_th.get('platforms', {})
                    platform_list = []
                    if platforms.get('windows'): platform_list.append('Windows')
                    if platforms.get('mac'): platform_list.append('Mac')
                    if platforms.get('linux'): platform_list.append('Linux')
                    platform_str = ', '.join(platform_list) if platform_list else None
                    
                    # Extract price info
                    price_overview = steam_details_th.get('price_overview', {})
                    price_str = price_overview.get('final_formatted') if price_overview else None
                    
                    # Extract video URL (first movie)
                    movies = steam_details_th.get('movies', [])
                    video_url = movies[0].get('webm', {}).get('480') if movies else None
                    if not video_url and movies:
                        video_url = movies[0].get('mp4', {}).get('480')
                    
                    # Parse release date
                    release_date_str = steam_details_th.get('release_date', {}).get('date')
                    release_date_obj = None
                    if release_date_str:
                        try:
                            from datetime import datetime
                            # Try different date formats
                            for fmt in ['%d %b, %Y', '%b %d, %Y', '%Y-%m-%d', '%d %B, %Y']:
                                try:
                                    release_date_obj = datetime.strptime(release_date_str, fmt).date()
                                    break
                                except ValueError:
                                    continue
                        except:
                            pass
                    
                    # Use Steam API data (with Thai language support)
                    new_game = models.Game(
                        title=steam_details_th.get('name'),
                        description=final_desc,  # Thai or translated description
                        genre=", ".join([g["description"] for g in steam_details_th.get("genres", [])[:3]]),
                        image_url=steam_details_th.get('header_image'),
                        release_date=release_date_obj,
                        developer=", ".join(steam_details_th.get('developers', [])),
                        publisher=", ".join(steam_details_th.get('publishers', [])),
                        platform=platform_str,
                        price=price_str,
                        video=video_url
                    )
                
                db.add(new_game)
                imported_count += 1
                
                # Commit every 10 games to avoid losing progress
                if imported_count % 10 == 0:
                    db.commit()
                
                # Be nice to APIs - add delay
                time.sleep(1.5)
                
            except Exception as e:
                print(f"Error importing game {app_id}: {e}")
                failed_count += 1
                continue
        
        # Final commit
        db.commit()
        
        return {
            "success": True,
            "message": f"Batch import completed",
            "imported": imported_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "total_processed": imported_count + skipped_count + failed_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during batch import: {str(e)}"
        )

