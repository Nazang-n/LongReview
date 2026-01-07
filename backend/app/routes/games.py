from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, aliased
from sqlalchemy import text, and_, case
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..utils.tag_translator import translate_tag
from datetime import date

router = APIRouter(
    prefix="/api/games",
    tags=["games"]
)


def serialize_game(game: models.Game) -> dict:
    """Convert Game model to dict with proper date serialization"""
    # Try to get steam_app_id - it may not be loaded if backend wasn't restarted
    steam_app_id = getattr(game, 'steam_app_id', None)
    
    # Translate genres
    genre_th = None
    if game.genre:
        genres = [g.strip() for g in game.genre.split(',')]
        genres_th = [translate_tag(g, 'genre') for g in genres]
        genre_th = ", ".join(genres_th)
    
    return {
        "id": game.id,
        "title": game.title,
        "description": game.description,
        "genre": game.genre,
        "genre_th": genre_th,
        "rating": game.rating,
        "image_url": game.image_url,
        "release_date": game.release_date.isoformat() if game.release_date else None,
        "developer": game.developer,
        "publisher": game.publisher,
        "platform": game.platform,
        "price": game.price,
        "video": game.video,
        "about_game_th": game.about_game_th,
        "app_id": steam_app_id,
        "player_modes": []  # Default empty list
    }


@router.get("/", response_model=List[schemas.Game])
def get_games(
    skip: int = 0,
    limit: int = 100,
    tags: Optional[str] = Query(None, description="Comma-separated tag IDs to filter by"),
    db: Session = Depends(get_db)
):
    """
    Get all games with pagination, sorted by newest release date first.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    - **tags**: Comma-separated tag IDs to filter by (e.g., "1,2,3")
    """
    query = db.query(models.Game)
    
    # Apply tag filtering if provided
    if tags:
        tag_ids = [int(tid.strip()) for tid in tags.split(',') if tid.strip().isdigit()]
        
        if tag_ids:
            # Get games that have ALL specified tags (AND logic)
            # For each tag, join with game_tags and filter
            for tag_id in tag_ids:
                game_tag_alias = aliased(models.GameTag)
                query = query.join(
                    game_tag_alias,
                    and_(
                        models.Game.id == game_tag_alias.game_id,
                        game_tag_alias.tag_id == tag_id
                    )
                )
    
    # Apply ordering and pagination
    games = query.order_by(models.Game.release_date.desc()).offset(skip).limit(limit).all()
    
    # Fetch player modes for these games
    results = []
    if games:
        game_ids = [g.id for g in games]
        
        # Query player mode tags
        pm_tags = db.query(models.GameTag.game_id, models.Tag.name)\
            .join(models.Tag, models.GameTag.tag_id == models.Tag.id)\
            .filter(models.GameTag.game_id.in_(game_ids))\
            .filter(models.Tag.type == 'player_mode')\
            .all()
            
        # Group by game_id
        pm_map = {}
        for gid, tname in pm_tags:
            if gid not in pm_map:
                pm_map[gid] = []
            pm_map[gid].append(tname)
            
        # Serialize and attach
        for game in games:
            g_dict = serialize_game(game)
            g_dict['player_modes'] = pm_map.get(game.id, [])
            results.append(g_dict)
            
    return results


@router.get("/count")
def get_games_count(
    tags: Optional[str] = Query(None, description="Comma-separated tag IDs to filter by"),
    db: Session = Depends(get_db)
):
    """
    Get total count of games in database, optionally filtered by tags.
    """
    query = db.query(models.Game)
    
    # Apply tag filtering if provided (same logic as get_games)
    if tags:
        tag_ids = [int(tid.strip()) for tid in tags.split(',') if tid.strip().isdigit()]
        
        if tag_ids:
            for tag_id in tag_ids:
                game_tag_alias = aliased(models.GameTag)
                query = query.join(
                    game_tag_alias,
                    and_(
                        models.Game.id == game_tag_alias.game_id,
                        game_tag_alias.tag_id == tag_id
                    )
                )
    
    count = query.count()
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
        models.Game.title.ilike(f"%{query}%")
    ).order_by(models.Game.release_date.desc()).offset(skip).limit(limit).all()
    return games


@router.post("/translate/batch")
def batch_translate_games(
    limit: int = Query(10000, description="Number of games to translate", ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """
    Batch translate all games that don't have Thai descriptions.
    
    This will:
    1. Find all games where about_game_th is NULL or empty
    2. Translate their English description to Thai
    3. Save the Thai translation to the database
    """
    from ..utils.translator import translator
    import re
    
    # Find ALL games (we'll check language in the loop)
    all_games = db.query(models.Game).limit(limit).all()
    
    games_to_translate = []
    
    # Check each game to see if about_game_th needs translation
    for game in all_games:
        needs_translation = False
        
        # Case 1: about_game_th is NULL or empty
        if not game.about_game_th or game.about_game_th.strip() == "":
            needs_translation = True
        else:
            # Case 2: about_game_th contains English text (check for common English words)
            # Simple heuristic: if it contains mostly English characters and common English words
            text = game.about_game_th.lower()
            english_indicators = ['the', 'and', 'for', 'with', 'from', 'this', 'that', 'your', 'you', 'are', 'have', 'will']
            english_word_count = sum(1 for word in english_indicators if f' {word} ' in f' {text} ')
            
            # If we find 2+ common English words, it's probably English
            if english_word_count >= 2:
                needs_translation = True
        
        if needs_translation:
            games_to_translate.append(game)
    
    if not games_to_translate:
        return {
            "message": "No games need translation",
            "translated": 0,
            "failed": 0
        }
    
    print(f"Found {len(games_to_translate)} games to translate")
    
    translated_count = 0
    failed_count = 0
    failed_games = []
    
    for game in games_to_translate:
        try:
            # Determine source text for translation
            source_text = None
            
            # Priority 1: Use about_game_th if it has English text
            if game.about_game_th and game.about_game_th.strip():
                source_text = game.about_game_th
                print(f"Translating game {game.id}: {game.title} (from about_game_th)")
            # Priority 2: Use description if about_game_th is empty
            elif game.description and game.description.strip():
                source_text = game.description
                print(f"Translating game {game.id}: {game.title} (from description)")
            else:
                print(f"Skipping game {game.id}: {game.title} - No text to translate")
                continue
            
            # Translate to Thai
            thai_translation = translator.translate_to_thai(source_text)
            
            # Save to database
            if thai_translation and thai_translation != source_text:
                game.about_game_th = thai_translation
                db.commit()
                translated_count += 1
                print(f"  ✓ Translated and saved")
            else:
                failed_count += 1
                failed_games.append({"id": game.id, "title": game.title, "reason": "Translation returned empty or same as original"})
                print(f"  ✗ Translation failed or returned same text")
                
        except Exception as e:
            failed_count += 1
            failed_games.append({"id": game.id, "title": game.title, "reason": str(e)})
            print(f"  ✗ Error: {e}")
            db.rollback()
    
    return {
        "message": f"Batch translation completed",
        "total_found": len(games_to_translate),
        "translated": translated_count,
        "failed": failed_count,
        "failed_games": failed_games[:10]  # Return first 10 failed games
    }


