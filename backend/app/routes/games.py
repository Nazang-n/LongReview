from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, aliased
from sqlalchemy import text, and_, case, or_
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..utils.tag_translator import translate_tag
from datetime import date

router = APIRouter(
    prefix="/api/games",
    tags=["games"]
)


def serialize_game(game: models.Game, sentiment: Optional[models.GameSentiment] = None) -> dict:
    """Convert Game model to dict with proper date serialization"""
    # Try to get steam_app_id - it may not be loaded if backend wasn't restarted
    steam_app_id = getattr(game, 'steam_app_id', None)
    
    # Translate genres
    genre_th = None
    if game.genre:
        genres = [g.strip() for g in game.genre.split(',')]
        genres_th = [translate_tag(g, 'genre') for g in genres]
        genre_th = ", ".join(genres_th)
        
    # Determine review type from sentiment if available, else fallback to rating
    review_type = "mixed"
    if sentiment and sentiment.review_score_desc:
        desc = sentiment.review_score_desc.lower()
        if 'positive' in desc:
            review_type = 'positive'
        elif 'negative' in desc:
            review_type = 'negative'
        else:
            review_type = 'mixed'
    elif game.rating:
        review_type = "positive" if game.rating >= 7 else "mixed" if game.rating >= 4 else "negative"
    
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
        "player_modes": [],  # Default empty list
        "review_type": review_type
    }


@router.get("/", response_model=List[schemas.Game])
def get_games(
    skip: int = 0,
    limit: int = 100,
    tags: Optional[str] = Query(None, description="Comma-separated tag IDs to filter by"),
    sort_by: Optional[str] = Query("newest", description="Sort by: newest, popular, rating"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: positive"),
    year: Optional[int] = Query(None, description="Filter by release year"),
    db: Session = Depends(get_db)
):
    """
    Get all games with pagination, sorted by newest release date first.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    - **tags**: Comma-separated tag IDs to filter by (e.g., "1,2,3")
    - **sort_by**: Sort order ("newest", "popular", "rating")
    - **sentiment**: Filter by sentiment ("positive" for >= 80% positive reviews)
    - **year**: Filter by release year
    """
    
    query = db.query(models.Game)

    # Handle GameSentiment Join (Filter or Sort)
    if sentiment == "positive":
        # Filter mode: INNER JOIN + Filter
        query = query.join(models.GameSentiment, models.Game.id == models.GameSentiment.game_id)
        query = query.filter(models.GameSentiment.positive_percent >= 70)
    elif sort_by in ["popular", "rating"]:
        # Sort-only mode: OUTER JOIN (to include all games)
        query = query.outerjoin(models.GameSentiment, models.Game.id == models.GameSentiment.game_id)
        
    # Apply Year Release Filter
    if year:
        from datetime import date
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        query = query.filter(
            models.Game.release_date >= start_date,
            models.Game.release_date <= end_date
        )
    
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
    
    # Priority Sort: If filtering by single tag, prioritize games where that tag is PRIMARY (first in genre list)
    primary_tag_sort = None
    if tags:
        tag_ids = [int(tid.strip()) for tid in tags.split(',') if tid.strip().isdigit()]
        if len(tag_ids) == 1:
            tag = db.query(models.Tag).filter(models.Tag.id == tag_ids[0]).first()
            if tag and tag.type == 'genre':
                # Case: 0 if match (first), 1 if not match (sort ascending puts 0 first)
                primary_tag_sort = case(
                    (models.Game.genre.ilike(f"{tag.name}%"), 0),
                    else_=1
                )

    if sort_by == "popular":
        # Sort by total_reviews from GameSentiment (descending)
        if primary_tag_sort is not None:
            # Prioritize Popularity first, then Primary Tag status as tie-breaker
            query = query.order_by(models.GameSentiment.total_reviews.desc().nullslast(), primary_tag_sort)
        else:
            query = query.order_by(models.GameSentiment.total_reviews.desc().nullslast())
    elif sort_by == "rating":
        # Sort by rating descending (nulls last), then by total_reviews descending
        if primary_tag_sort is not None:
            query = query.order_by(
                primary_tag_sort,
                models.Game.rating.desc().nullslast(),
                models.GameSentiment.total_reviews.desc().nullslast()
            )
        else:
            query = query.order_by(
                models.Game.rating.desc().nullslast(),
                models.GameSentiment.total_reviews.desc().nullslast()
            )
    else:
        # Default: newest first
        if primary_tag_sort is not None:
            query = query.order_by(primary_tag_sort, models.Game.release_date.desc().nullslast())
        else:
            query = query.order_by(models.Game.release_date.desc().nullslast())
        
    games = query.offset(skip).limit(limit).all()
    
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


@router.get("/{game_id}/similar", response_model=List[dict])
def get_similar_games(game_id: int, limit: int = 12, db: Session = Depends(get_db)):
    """
    Get similar games based on genre overlap.
    Returns top {limit} games sharing the most tags/genres.
    """
    # 1. Get current game
    current_game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not current_game:
        return []
        
    if not current_game.genre:
        return []

    # 2. Extract current genres
    # Define generic tags to ignore in similarity calculation
    ignored_tags = {'free to play', 'early access', 'action', 'adventure', 'indie', 'casual', 'simulation'}
    
    current_genres = set([g.strip().lower() for g in current_game.genre.split(',') if g.strip()])
    # Filter out ignored tags IF there are other specific tags available
    # (If a game ONLY has ignored tags, we keep them to find something)
    filtered_current = {g for g in current_genres if g not in ignored_tags}
    if not filtered_current:
        filtered_current = current_genres # Fallback if only generic tags exist
    
    # 3. Fetch all other games
    all_games = db.query(models.Game).filter(models.Game.id != game_id).all()
    
    scores = []
    for game in all_games:
        if not game.genre:
            continue
            
        game_genres = set([g.strip().lower() for g in game.genre.split(',') if g.strip()])
        filtered_game = {g for g in game_genres if g not in ignored_tags}
        if not filtered_game:
            filtered_game = game_genres
        
        # Calculate overlap on FILTERED tags
        overlap = len(filtered_current.intersection(filtered_game))
        
        # Secondary sort metric: Jaccard similarity (overlap / union) to prefer closer matches
        # e.g. (RPG, Anime) matches (RPG, Anime) better than (RPG, Anime, Strategy, Sci-fi)
        union_size = len(filtered_current.union(filtered_game))
        jaccard = overlap / union_size if union_size > 0 else 0
        
        if overlap > 0:
            scores.append((overlap, jaccard, game))
            
    # 4. Sort by overlap (desc) then Jaccard (desc)
    scores.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    top_games = []
    
    # Optimize: fetch required sentiment records in one go
    top_game_ids = [item[2].id for item in scores[:limit]]
    sentiments = db.query(models.GameSentiment).filter(models.GameSentiment.game_id.in_(top_game_ids)).all()
    sentiment_map = {s.game_id: s for s in sentiments}
    
    for item in scores[:limit]:
        g = item[2]
        # Pass sentiment data to serializer
        game_dict = serialize_game(g, sentiment_map.get(g.id))
        top_games.append(game_dict)
    
    return top_games


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
            # Case 2: Check if it already has Thai characters
            # If it has Thai characters, assume it is translated (skip it)
            has_thai = bool(re.search(r'[\u0E00-\u0E7F]', game.about_game_th))
            
            if has_thai:
                needs_translation = False
            else:
                # No Thai characters, assume it needs translation
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




