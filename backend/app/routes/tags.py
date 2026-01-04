from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/tags",
    tags=["tags"]
)


@router.post("/migrate")
def migrate_tags_from_games(db: Session = Depends(get_db)):
    """
    Migrate existing genre and platform data from games to tags system.
    
    This will:
    1. Extract unique genres and platforms from all games
    2. Create tag entries for each
    3. Create game_tags relationships
    """
    try:
        # Get all games
        games = db.query(models.Game).all()
        
        # Collect unique genres and platforms
        unique_genres = set()
        unique_platforms = set()
        
        for game in games:
            if game.genre:
                genres = [g.strip() for g in game.genre.split(',') if g.strip()]
                unique_genres.update(genres)
            
            if game.platform:
                platforms = [p.strip() for p in game.platform.split(',') if p.strip()]
                unique_platforms.update(platforms)
        
        # Create genre tags
        genre_tag_map = {}
        for genre_name in sorted(unique_genres):
            existing_tag = db.query(models.Tag).filter(
                models.Tag.name == genre_name,
                models.Tag.type == 'genre'
            ).first()
            
            if existing_tag:
                genre_tag_map[genre_name] = existing_tag.id
            else:
                new_tag = models.Tag(name=genre_name, type='genre')
                db.add(new_tag)
                db.flush()
                genre_tag_map[genre_name] = new_tag.id
        
        # Create platform tags
        platform_tag_map = {}
        for platform_name in sorted(unique_platforms):
            existing_tag = db.query(models.Tag).filter(
                models.Tag.name == platform_name,
                models.Tag.type == 'platform'
            ).first()
            
            if existing_tag:
                platform_tag_map[platform_name] = existing_tag.id
            else:
                new_tag = models.Tag(name=platform_name, type='platform')
                db.add(new_tag)
                db.flush()
                platform_tag_map[platform_name] = new_tag.id
        
        db.commit()
        
        # Create game_tags relationships
        game_tag_count = 0
        for game in games:
            # Link genres
            if game.genre:
                genres = [g.strip() for g in game.genre.split(',') if g.strip()]
                for genre_name in genres:
                    if genre_name in genre_tag_map:
                        existing_link = db.query(models.GameTag).filter(
                            models.GameTag.game_id == game.id,
                            models.GameTag.tag_id == genre_tag_map[genre_name]
                        ).first()
                        
                        if not existing_link:
                            game_tag = models.GameTag(
                                game_id=game.id,
                                tag_id=genre_tag_map[genre_name]
                            )
                            db.add(game_tag)
                            game_tag_count += 1
            
            # Link platforms
            if game.platform:
                platforms = [p.strip() for p in game.platform.split(',') if p.strip()]
                for platform_name in platforms:
                    if platform_name in platform_tag_map:
                        existing_link = db.query(models.GameTag).filter(
                            models.GameTag.game_id == game.id,
                            models.GameTag.tag_id == platform_tag_map[platform_name]
                        ).first()
                        
                        if not existing_link:
                            game_tag = models.GameTag(
                                game_id=game.id,
                                tag_id=platform_tag_map[platform_name]
                            )
                            db.add(game_tag)
                            game_tag_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": "Migration completed successfully",
            "genres_count": len(unique_genres),
            "platforms_count": len(unique_platforms),
            "game_tags_count": game_tag_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@router.get("/")
def get_tags(
    type: Optional[str] = Query(None, description="Filter by type: genre, platform, player_mode"),
    db: Session = Depends(get_db)
):
    """
    Get all tags, optionally filtered by type.
    
    - **type**: Filter by tag type (genre, platform, player_mode)
    
    Returns list of tags with their IDs, English names, and Thai translations.
    """
    from ..utils.tag_translator import translate_tag
    
    query = db.query(models.Tag)
    
    if type:
        query = query.filter(models.Tag.type == type)
    
    tags = query.order_by(models.Tag.name).all()
    
    return {
        "success": True,
        "tags": [
            {
                "id": tag.id,
                "name": tag.name,
                "name_th": translate_tag(tag.name, tag.type),
                "type": tag.type
            } for tag in tags
        ]
    }


@router.get("/stats")
def get_tag_stats(db: Session = Depends(get_db)):
    """
    Get statistics about tags - how many games have each tag.
    
    Returns tags grouped by type with game counts and Thai translations.
    """
    from sqlalchemy import func
    from ..utils.tag_translator import translate_tag
    
    # Get tag counts
    tag_stats = db.query(
        models.Tag.id,
        models.Tag.name,
        models.Tag.type,
        func.count(models.GameTag.game_id).label('game_count')
    ).outerjoin(
        models.GameTag, models.Tag.id == models.GameTag.tag_id
    ).group_by(
        models.Tag.id, models.Tag.name, models.Tag.type
    ).order_by(
        models.Tag.type, models.Tag.name
    ).all()
    
    # Group by type
    result = {
        "genres": [],
        "platforms": [],
        "player_modes": []
    }
    
    for tag_id, name, tag_type, game_count in tag_stats:
        tag_data = {
            "id": tag_id,
            "name": name,
            "name_th": translate_tag(name, tag_type),
            "game_count": game_count
        }
        
        if tag_type == "genre":
            result["genres"].append(tag_data)
        elif tag_type == "platform":
            result["platforms"].append(tag_data)
        elif tag_type == "player_mode":
            result["player_modes"].append(tag_data)
    
    return {
        "success": True,
        "stats": result
    }
