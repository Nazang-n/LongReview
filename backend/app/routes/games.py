from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session, aliased
from sqlalchemy import text, and_, case, or_
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..utils.tag_translator import translate_tag
from ..utils.price_converter import convert_usd_to_thb
from datetime import date

router = APIRouter(
    prefix="/api/games",
    tags=["games"]
)


def serialize_game(game: models.Game, sentiment: Optional[models.GameSentiment] = None, genres_list: Optional[List[str]] = None) -> dict:
    """Convert Game model to dict with proper date serialization"""
    # Try to get steam_app_id - it may not be loaded if backend wasn't restarted
    steam_app_id = getattr(game, 'steam_app_id', None)
    
    # Translate genres
    genre_th = None
    
    # Use provided genres_list if available (from GameTags), else fallback to game.genre string
    genres = []
    if genres_list is not None:
        genres = genres_list
    elif game.genre:
        genres = [g.strip() for g in game.genre.split(',')]
        
    # Filter out 'Massively Multiplayer' as it's handled in player_modes
    genres = [g for g in genres if g.lower() != 'massively multiplayer']
        
    if genres:
        genres_th = [translate_tag(g, 'genre') for g in genres]
        genre_th = ", ".join(genres_th)
        
    # Determine review type from sentiment if available, else fallback to rating
    review_type = "mixed"
    sentiment_percent = None
    total_reviews = None
    
    # Use provided sentiment OR fall back to relationship
    game_sentiment = sentiment or getattr(game, 'sentiment', None)
    
    if game_sentiment:
        sentiment_percent = game_sentiment.positive_percent
        total_reviews = game_sentiment.total_reviews
        if game_sentiment.review_score_desc:
            desc = game_sentiment.review_score_desc.lower()
            if 'positive' in desc:
                review_type = 'positive'
            elif 'negative' in desc:
                review_type = 'negative'
            else:
                review_type = 'mixed'
    elif game.rating:
        review_type = "positive" if game.rating >= 7 else "mixed" if game.rating >= 4 else "negative"
    
    result = {
        "id": game.id,
        "title": game.title,
        "description": game.description,
        "genre": ", ".join(genres) if genres else game.genre,
        "genre_th": genre_th,
        "rating": game.rating,
        "image_url": game.image_url,
        "release_date": game.release_date.isoformat() if game.release_date else None,
        "developer": game.developer,
        "publisher": game.publisher,
        "platform": game.platform,
        "price": game.price,
        "price_thb": convert_usd_to_thb(game.price),
        "video": game.video,
        "screenshots": game.screenshots,
        "about_game_th": game.about_game_th,
        "app_id": steam_app_id,
        "player_modes": [],  # Default empty list
        "review_type": review_type,
        "sentiment_percent": sentiment_percent,
        "total_reviews": total_reviews
    }
    print(f"DEBUG: serialize_game returning 'screenshots' field: {'screenshots' in result}")
    return result


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

    # Handle GameSentiment Join
    if sentiment == "positive":
        # Filter mode: INNER JOIN + Filter
        query = query.join(models.GameSentiment, models.Game.id == models.GameSentiment.game_id)
        query = query.filter(models.GameSentiment.positive_percent >= 70)
    else:
        # Sort or data mode: OUTER JOIN (to include all games)
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

    if sort_by == "popular_hero":
        # Strict logic for Home Page Hero Slider
        # 1. Force filter to include only Very Positive games (>= 80%)
        # 2. AND strict filter for popularity: Must have at least 1,000 reviews
        query = query.filter(
            models.GameSentiment.positive_percent >= 80,
            models.GameSentiment.total_reviews >= 1000
        )
        
        # Strict Sort: Total Reviews DESC -> Positive Percent DESC
        query = query.order_by(
            models.GameSentiment.total_reviews.desc().nullslast(),
            models.GameSentiment.positive_percent.desc().nullslast()
        )

    elif sort_by == "popular":
        # Standard Popular Sort (for categories etc.) - Only "Positive" labeled games
        query = query.filter(models.GameSentiment.review_score_desc.ilike('%positive%'))
        
        # Strict Sort: Total Reviews DESC -> Positive Percent DESC
        query = query.order_by(
            models.GameSentiment.total_reviews.desc().nullslast(),
            models.GameSentiment.positive_percent.desc().nullslast()
        )
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
    
    # Fetch player modes AND genres for these games
    results = []
    if games:
        game_ids = [g.id for g in games]
        
        # Query tags (both player_mode and genre)
        tags_data = db.query(models.GameTag.game_id, models.Tag.name, models.Tag.type)\
            .join(models.Tag, models.GameTag.tag_id == models.Tag.id)\
            .filter(models.GameTag.game_id.in_(game_ids))\
            .filter(models.Tag.type.in_(['player_mode', 'genre']))\
            .all()
            
        # Group by game_id
        pm_map = {}
        genre_map = {}
        
        for gid, tname, ttype in tags_data:
            if ttype == 'player_mode':
                if gid not in pm_map:
                    pm_map[gid] = []
                pm_map[gid].append(tname)
            elif ttype == 'genre':
                if gid not in genre_map:
                    genre_map[gid] = []
                genre_map[gid].append(tname)
            
        # Serialize and attach
        for game in games:
            # Pass full genre list from DB relationships
            game_genres = genre_map.get(game.id, None)
            g_dict = serialize_game(game, genres_list=game_genres)
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
    
    # Fetch genres from GameTag
    genre_tags = db.query(models.Tag.name)\
        .join(models.GameTag, models.GameTag.tag_id == models.Tag.id)\
        .filter(models.GameTag.game_id == game_id)\
        .filter(models.Tag.type == 'genre')\
        .all()
    
    genre_list = [g[0] for g in genre_tags] if genre_tags else None

    # Fetch player modes
    pm_tags = db.query(models.Tag.name)\
        .join(models.GameTag, models.GameTag.tag_id == models.Tag.id)\
        .filter(models.GameTag.game_id == game_id)\
        .filter(models.Tag.type == 'player_mode')\
        .all()
    
    pm_list = [t[0] for t in pm_tags] if pm_tags else []
    
    game_dict = serialize_game(game, genres_list=genre_list)
    game_dict["player_modes"] = pm_list
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
    
    # Attach empty player_modes for schema validation
    setattr(db_game, 'player_modes', [])
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
    
    # Attach player_modes for schema validation
    setattr(db_game, 'player_modes', [])
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
    from sqlalchemy import and_
    
    # Handle multiple spaces by splitting into words
    words = query.strip().split()
    
    # Create an ILIKE condition for each word
    filters = [models.Game.title.ilike(f"%{word}%") for word in words]
    
    if filters:
        games = db.query(models.Game).filter(
            and_(*filters)
        ).order_by(models.Game.release_date.desc()).offset(skip).limit(limit).all()
    else:
        games = []
    
    results = []
    if games:
        # For search, we can probably skip heavy tag fetching or do it if needed.
        # Let's just return basic info + empty player_modes to be fast and safe
        # Or reuse serialize_game for consistency
        for game in games:
            g_dict = serialize_game(game)
            # We didn't fetch tags, so pass empty list or whatever serialize_game behavior is
            # serialize_game handles missing tags gracefully?
            # get_games logic fetches tags separately.
            g_dict['player_modes'] = [] 
            results.append(g_dict)
            
    return results


def run_batch_translation_bg(limit: int, task_id: str = None):
    from ..database import SessionLocal
    from ..utils.translator import translator
    from .. import models
    import re
    import time
    
    print(f"[BG Translater] Starting batch translation process for up to {limit} games. Task ID: {task_id}")
    db = SessionLocal()
    try:
        all_games = db.query(models.Game).limit(limit).all()
        games_to_translate = []
        for game in all_games:
            needs_translation = False
            if not game.about_game_th or game.about_game_th.strip() == "":
                needs_translation = True
            else:
                has_thai = bool(re.search(r'[\u0E00-\u0E7F]', game.about_game_th))
                if not has_thai:
                    needs_translation = True
            
            if needs_translation:
                games_to_translate.append(game)
        
        print(f"[BG Translater] Found {len(games_to_translate)} games needing translation.")
        
        translated_count = 0
        failed_count = 0
        
        for game in games_to_translate:
            try:
                source_text = None
                if game.about_game_th and game.about_game_th.strip():
                    source_text = game.about_game_th
                elif game.description and game.description.strip():
                    source_text = game.description
                else:
                    continue
                
                print(f"[BG Translater] Translating game {game.id}: {game.title}")
                thai_translation = translator.translate_to_thai(source_text)
                
                if thai_translation and thai_translation != source_text:
                    game.about_game_th = thai_translation
                    db.commit()
                    translated_count += 1
                    print(f"  ✓ Processed game {game.id}")
                else:
                    failed_count += 1
                
                # Respect Gemini free tier: wait 4s between requests
                time.sleep(4)
                
            except Exception as e:
                db.rollback()
                failed_count += 1
                print(f"[BG Translater] Error on game {game.id}: {e}")
                
        if task_id:
            from ..services.task_manager import TaskManager
            TaskManager.update_task_success(task_id, {
                "total_found": len(games_to_translate),
                "translated": translated_count,
                "failed": failed_count
            })
                
    except Exception as e:
        print(f"[BG Translater] Critical Error: {e}")
        if task_id:
            from ..services.task_manager import TaskManager
            TaskManager.update_task_error(task_id, str(e))
    finally:
        db.close()
        print(f"[BG Translater] Finished batch translation run.")


@router.post("/translate/batch")
def batch_translate_games(
    background_tasks: BackgroundTasks,
    limit: int = Query(10000, description="Number of games to translate", ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """
    Trigger a background task to batch translate all games that don't have Thai descriptions.
    """
    from ..services.task_manager import TaskManager
    task_id = TaskManager.create_task("แปลภาษาเกม")
    background_tasks.add_task(run_batch_translation_bg, limit, task_id)
    
    return {
        "message": "Batch translation started in the background",
        "total_queued_limit": limit,
        "status": "processing",
        "task_id": task_id
    }




