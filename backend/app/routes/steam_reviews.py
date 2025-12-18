from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from .. import models
from ..database import get_db
from ..steam_api import SteamAPIClient

router = APIRouter(
    prefix="/api/steam/reviews",
    tags=["steam-reviews"]
)


@router.post("/import/game/{game_id}")
def import_reviews_for_game(
    game_id: int,
    language: str = Query("all", description="Language filter (all, thai, english)"),
    max_reviews: int = Query(100, description="Maximum reviews to import", ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Auto-import reviews using steam_app_id from game table
    
    - **game_id**: Your database game ID
    - **language**: Language filter (all, thai, english)
    - **max_reviews**: Maximum number of reviews to import (1-1000)
    
    Example: POST /api/steam/reviews/import/game/1?language=all&max_reviews=100
    """
    try:
        # Get game with steam_app_id
        game = db.query(models.Game).filter(models.Game.id == game_id).first()
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game with id {game_id} not found"
            )
        
        if not game.steam_app_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Game '{game.title}' does not have steam_app_id. Please re-import the game."
            )
        
        steam_app_id = int(game.steam_app_id)
        
        # Fetch reviews from Steam
        print(f"📥 Fetching reviews for {game.title} (Steam App {steam_app_id}, Game ID: {game_id})...")
        steam_reviews = SteamAPIClient.get_all_reviews(
            app_id=steam_app_id,
            language=language,
            max_reviews=max_reviews
        )
        
        if not steam_reviews:
            return {
                "success": False,
                "message": "No reviews found or error fetching from Steam",
                "game_title": game.title,
                "steam_app_id": steam_app_id,
                "imported": 0,
                "skipped": 0,
                "failed": 0
            }
        
        # Debug: Show what Steam sent
        unique_steam_ids = set(r.get('recommendationid') for r in steam_reviews)
        print(f"📊 Steam API returned {len(steam_reviews)} reviews ({len(unique_steam_ids)} unique)")
        
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        
        for steam_review in steam_reviews:
            try:
                recommendation_id = steam_review.get('recommendationid')
                
                # Check if review already exists
                existing_review = db.query(models.Review).filter(
                    models.Review.steam_id == recommendation_id
                ).first()
                
                if existing_review:
                    skipped_count += 1
                    continue
                
                # Convert Unix timestamp to datetime
                created_timestamp = steam_review.get('timestamp_created')
                created_at = datetime.fromtimestamp(created_timestamp) if created_timestamp else None
                
                # Extract author info for display name
                author = steam_review.get('author', {})
                
                # Create new review (only using columns that exist in DB)
                new_review = models.Review(
                    game_id=game_id,
                    steam_id=recommendation_id,
                    content=steam_review.get('review', ''),
                    owner=f"Steam User {author.get('steamid', 'Unknown')[-4:]}",
                    voted_up=steam_review.get('voted_up', True),
                    created_at=created_at
                )
                
                db.add(new_review)
                imported_count += 1
                
                # Commit every 50 reviews
                if imported_count % 50 == 0:
                    db.commit()
                    print(f"   ✓ Imported {imported_count} reviews...")
                
            except Exception as e:
                print(f"   ✗ Error importing review {recommendation_id}: {e}")
                failed_count += 1
                continue
        
        # Final commit
        db.commit()
        
        print(f"✅ Import completed: {imported_count} imported, {skipped_count} skipped, {failed_count} failed")
        
        return {
            "success": True,
            "message": "Review import completed",
            "game_title": game.title,
            "steam_app_id": steam_app_id,
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
            detail=f"Error importing reviews: {str(e)}"
        )


@router.post("/import/batch")
def import_reviews_batch(
    language: str = Query("all", description="Language filter"),
    max_reviews_per_game: int = Query(100, description="Max reviews per game", ge=1, le=500),
    limit: int = Query(10, description="Number of games to process", ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Batch import reviews for multiple games that have steam_app_id
    
    - **language**: Language filter (all, thai, english)
    - **max_reviews_per_game**: Maximum reviews to import per game
    - **limit**: Number of games to process
    
    Example: POST /api/steam/reviews/import/batch?language=all&max_reviews_per_game=50&limit=5
    """
    try:
        # Get games that have steam_app_id but no reviews yet
        games = db.query(models.Game).filter(
            models.Game.steam_app_id.isnot(None)
        ).limit(limit).all()
        
        if not games:
            return {
                "success": False,
                "message": "No games with steam_app_id found",
                "processed": 0,
                "total_imported": 0
            }
        
        total_imported = 0
        processed_count = 0
        results = []
        
        for game in games:
            try:
                steam_app_id = int(game.steam_app_id)
                print(f"\n📥 Processing {game.title} (Steam App {steam_app_id})...")
                
                steam_reviews = SteamAPIClient.get_all_reviews(
                    app_id=steam_app_id,
                    language=language,
                    max_reviews=max_reviews_per_game
                )
                
                print(f"   📊 Steam returned {len(steam_reviews) if steam_reviews else 0} reviews")
                
                if not steam_reviews:
                    results.append({
                        "game_id": game.id,
                        "game_title": game.title,
                        "imported": 0,
                        "message": "No reviews found"
                    })
                    continue
                
                imported_count = 0
                
                for steam_review in steam_reviews:
                    try:
                        recommendation_id = steam_review.get('recommendationid')
                        
                        # Check if exists
                        existing = db.query(models.Review).filter(
                            models.Review.steam_id == recommendation_id
                        ).first()
                        
                        if existing:
                            continue
                        
                        created_timestamp = steam_review.get('timestamp_created')
                        created_at = datetime.fromtimestamp(created_timestamp) if created_timestamp else None
                        author = steam_review.get('author', {})
                        
                        new_review = models.Review(
                            game_id=game.id,
                            steam_id=recommendation_id,
                            content=steam_review.get('review', ''),
                            owner=f"Steam User {author.get('steamid', 'Unknown')[-4:]}",
                            voted_up=steam_review.get('voted_up', True),
                            created_at=created_at
                        )
                        
                        db.add(new_review)
                        imported_count += 1
                        
                    except Exception as e:
                        print(f"   ✗ Error: {e}")
                        continue
                
                db.commit()
                total_imported += imported_count
                processed_count += 1
                
                results.append({
                    "game_id": game.id,
                    "game_title": game.title,
                    "imported": imported_count
                })
                
                print(f"   ✓ Imported {imported_count} reviews for {game.title}")
                
            except Exception as e:
                print(f"   ✗ Error processing {game.title}: {e}")
                continue
        
        return {
            "success": True,
            "message": f"Batch import completed for {processed_count} games",
            "processed": processed_count,
            "total_imported": total_imported,
            "results": results
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch import: {str(e)}"
        )
