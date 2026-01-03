from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from datetime import date

router = APIRouter(
    prefix="/api/games",
    tags=["games"]
)


def serialize_game(game: models.Game) -> dict:
    """Convert Game model to dict with proper date serialization"""
    # Try to get steam_app_id - it may not be loaded if backend wasn't restarted
    steam_app_id = getattr(game, 'steam_app_id', None)
    
    return {
        "id": game.id,
        "title": game.title,
        "description": game.description,
        "genre": game.genre,
        "rating": game.rating,
        "image_url": game.image_url,
        "release_date": game.release_date.isoformat() if game.release_date else None,
        "developer": game.developer,
        "publisher": game.publisher,
        "platform": game.platform,
        "price": game.price,
        "video": game.video,
        "about_game_th": game.about_game_th,
        "app_id": steam_app_id
    }


@router.get("/", response_model=List[schemas.Game])
def get_games(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all games with pagination, sorted by newest release date first.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    games = db.query(models.Game).order_by(models.Game.release_date.desc()).offset(skip).limit(limit).all()
    return [serialize_game(game) for game in games]


@router.get("/count")
def get_games_count(db: Session = Depends(get_db)):
    """
    Get total count of games in database.
    
    Returns the total number of games for pagination.
    """
    count = db.query(models.Game).count()
    return {"total": count}


@router.get("/{game_id}", response_model=schemas.Game)
def get_game(game_id: int, db: Session = Depends(get_db)):
    """
    Get a specific game by ID.
    Auto-translates description to Thai if not already available.
    
    - **game_id**: The ID of the game to retrieve
    """
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found"
        )
    
    # Auto-translate to Thai if not available
    if not game.about_game_th and game.description:
        try:
            from ..utils.translator import translator
            print(f"Auto-translating game {game_id} description to Thai...")
            
            # Translate description to Thai
            thai_translation = translator.translate_to_thai(game.description)
            
            # Save to database for caching
            if thai_translation and thai_translation != game.description:
                game.about_game_th = thai_translation
                db.commit()
                db.refresh(game)
                print(f"Thai translation saved for game {game_id}")
        except Exception as e:
            print(f"Translation error for game {game_id}: {e}")
            # Continue without translation if it fails
    
    # Get steam_app_id using raw SQL and add to response
    result = db.execute(
        text("SELECT steam_app_id FROM game WHERE id = :game_id"),
        {"game_id": game_id}
    )
    row = result.fetchone()
    
    game_dict = serialize_game(game)
    game_dict["app_id"] = row[0] if row else None
    
    return game_dict


@router.post("/", response_model=schemas.Game, status_code=status.HTTP_201_CREATED)
def create_game(game: schemas.GameCreate, db: Session = Depends(get_db)):
    """
    Create a new game.
    
    - **game**: Game data to create
    """
    db_game = models.Game(**game.model_dump())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


@router.put("/{game_id}", response_model=schemas.Game)
def update_game(
    game_id: int,
    game: schemas.GameUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing game.
    
    - **game_id**: The ID of the game to update
    - **game**: Updated game data
    """
    db_game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if db_game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found"
        )
    
    # Update only provided fields
    update_data = game.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_game, key, value)
    
    db.commit()
    db.refresh(db_game)
    return db_game


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_game(game_id: int, db: Session = Depends(get_db)):
    """
    Delete a game.
    
    - **game_id**: The ID of the game to delete
    """
    db_game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if db_game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found"
        )
    
    db.delete(db_game)
    db.commit()
    return None


@router.get("/search/", response_model=List[schemas.Game])
def search_games(
    query: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Search games by title or description.
    
    - **query**: Search query string
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    games = db.query(models.Game).filter(
        (models.Game.title.ilike(f"%{query}%")) |
        (models.Game.description.ilike(f"%{query}%"))
    ).offset(skip).limit(limit).all()
    return games
