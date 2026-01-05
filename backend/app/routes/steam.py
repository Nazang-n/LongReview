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
        
        # Import translator
        from ..utils.translator import translator
        
        # Get English description
        english_desc = app_details.get("short_description")
        
        # Translate to Thai
        thai_desc = None
        if english_desc:
            thai_desc = translator.translate_to_thai(english_desc)
            print(f"DEBUG: English desc length: {len(english_desc) if english_desc else 0}")
            print(f"DEBUG: Thai desc length: {len(thai_desc) if thai_desc else 0}")
            print(f"DEBUG: Thai desc is same as English: {thai_desc == english_desc if thai_desc and english_desc else 'N/A'}")
        
        # Create new game
        new_game = models.Game(
            title=app_details.get("name"),
            description=english_desc,  # English description
            about_game_th=thai_desc,   # Thai translation
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
                # Check if game already exists (by title OR steam_app_id)
                existing_game = db.query(models.Game).filter(
                    (models.Game.title == game.get('name')) |
                    (models.Game.steam_app_id == int(app_id))
                ).first()
                
                if existing_game:
                    skipped_count += 1
                    continue
                
                # Fetch detailed info from Steam API (English for reliable date parsing)
                steam_details_en = SteamAPIClient.get_app_details(int(app_id), language="english", country_code="us")
                
                if not steam_details_en:
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
                    # Also fetch Thai version for Thai description (if available)
                    steam_details_th = SteamAPIClient.get_app_details(int(app_id), language="thai", country_code="th")
                    
                    # Import utilities
                    from ..utils.translator import translator
                    from ..utils.text_cleaner import clean_html_text
                    
                    # Try to get Thai description first, fallback to English + translation
                    thai_desc = None
                    english_desc = None
                    
                    # Get English description first
                    about_game_en = steam_details_en.get('about_the_game')
                    short_desc_en = steam_details_en.get('short_description')
                    
                    if about_game_en:
                        english_desc = clean_html_text(about_game_en)
                    elif short_desc_en:
                        english_desc = clean_html_text(short_desc_en)
                    
                    if steam_details_th:
                        # Try Thai about_the_game
                        about_game_th = steam_details_th.get('about_the_game')
                        if about_game_th:
                            cleaned_thai = clean_html_text(about_game_th)
                            # Verify it's actually Thai, not English
                            detected_lang = translator.detect_language(cleaned_thai)
                            if detected_lang == 'th':
                                thai_desc = cleaned_thai
                                print(f"   ✓ Using native Thai description")
                            else:
                                print(f"   ⚠ Steam Thai API returned {detected_lang}, not Thai. Will translate.")
                    
                    # If no Thai description, translate English
                    if not thai_desc and english_desc:
                        thai_desc = translator.translate_to_thai(english_desc)
                        print(f"   ⚡ Translated English description to Thai")
                    
                    # Extract platform info
                    platforms = steam_details_en.get('platforms', {})
                    platform_list = []
                    if platforms.get('windows'): platform_list.append('Windows')
                    if platforms.get('mac'): platform_list.append('Mac')
                    if platforms.get('linux'): platform_list.append('Linux')
                    platform_str = ', '.join(platform_list) if platform_list else None
                    
                    # Extract price info
                    price_overview = steam_details_en.get('price_overview', {})
                    price_str = price_overview.get('final_formatted') if price_overview else None
                    
                    # Extract video URL (first movie)
                    movies = steam_details_en.get('movies', [])
                    video_url = movies[0].get('webm', {}).get('480') if movies else None
                    if not video_url and movies:
                        video_url = movies[0].get('mp4', {}).get('480')
                    
                    # Parse release date (from English API for reliable parsing)
                    release_date_info = steam_details_en.get('release_date', {})
                    release_date_str = release_date_info.get('date')
                    coming_soon = release_date_info.get('coming_soon', False)
                    
                    # Debug: Print raw release date info
                    print(f"🔍 Game: {steam_details_en.get('name')}")
                    print(f"   Release date info: {release_date_info}")
                    print(f"   Date string: '{release_date_str}'")
                    print(f"   Coming soon: {coming_soon}")
                    
                    release_date_obj = None
                    if release_date_str and not coming_soon:
                        try:
                            from datetime import datetime
                            # Try different date formats that Steam uses
                            date_formats = [
                                '%d %b, %Y',      # "9 Jul, 2013"
                                '%b %d, %Y',      # "Jul 9, 2013"
                                '%d %B, %Y',      # "9 July, 2013"
                                '%B %d, %Y',      # "July 9, 2013"
                                '%Y-%m-%d',       # "2013-07-09"
                                '%d %b %Y',       # "9 Jul 2013" (without comma)
                                '%b %d %Y',       # "Jul 9 2013" (without comma)
                                '%Y',             # "2013" (year only)
                            ]
                            
                            for fmt in date_formats:
                                try:
                                    release_date_obj = datetime.strptime(release_date_str, fmt).date()
                                    print(f"   ✓ Parsed date '{release_date_str}' using format '{fmt}' -> {release_date_obj}")
                                    break
                                except ValueError:
                                    continue
                            
                            if not release_date_obj:
                                print(f"   ⚠ Failed to parse date: '{release_date_str}'")
                        except Exception as e:
                            print(f"   ⚠ Error parsing date '{release_date_str}': {e}")
                            pass
                    elif coming_soon:
                        print(f"   ⏳ Game is coming soon, skipping date")
                    else:
                        print(f"   ⚠ No release date string found")
                    
                    # Use Steam API data (English in description, Thai in about_game_th)
                    new_game = models.Game(
                        title=steam_details_en.get('name'),
                        description=english_desc,  # English description
                        about_game_th=thai_desc,   # Thai description (native or translated)
                        genre=", ".join([g["description"] for g in steam_details_en.get("genres", [])[:3]]),
                        image_url=steam_details_en.get('header_image'),
                        release_date=release_date_obj,
                        developer=", ".join(steam_details_en.get('developers', [])),
                        publisher=", ".join(steam_details_en.get('publishers', [])),
                        platform=platform_str,
                        price=price_str,
                        video=video_url,
                        steam_app_id=int(app_id)  # Store Steam App ID
                    )
                
                db.add(new_game)
                db.flush()  # Get the game ID
                
                # Extract and create player mode tags from categories
                categories = steam_details_en.get('categories', [])
                player_mode_tags = []
                
                for category in categories:
                    category_id = category.get('id')
                    # Single-player: category 2
                    # Multi-player: category 1
                    # Co-op: category 9, 24, 36, 37, 38
                    if category_id == 2:
                        player_mode_tags.append('Single-player')
                    elif category_id == 1:
                        player_mode_tags.append('Multi-player')
                    elif category_id in [9, 24, 36, 37, 38]:  # Various co-op modes
                        if 'Co-op' not in player_mode_tags:
                            player_mode_tags.append('Co-op')
                
                # Create/link player mode tags
                for mode_name in player_mode_tags:
                    # Check if tag exists
                    tag = db.query(models.Tag).filter(
                        models.Tag.name == mode_name,
                        models.Tag.type == 'player_mode'
                    ).first()
                    
                    if not tag:
                        tag = models.Tag(name=mode_name, type='player_mode')
                        db.add(tag)
                        db.flush()
                    
                    # Link game to tag
                    existing_link = db.query(models.GameTag).filter(
                        models.GameTag.game_id == new_game.id,
                        models.GameTag.tag_id == tag.id
                    ).first()
                    
                    if not existing_link:
                        game_tag = models.GameTag(game_id=new_game.id, tag_id=tag.id)
                        db.add(game_tag)
                
                # Auto-link Massively Multiplayer games to Multi-player tag
                genres = steam_details_en.get('genres', [])
                is_massively_multiplayer = any(g.get('description') == 'Massively Multiplayer' for g in genres)
                
                if is_massively_multiplayer and 'Multi-player' not in player_mode_tags:
                    # Find or create Multi-player tag
                    multiplayer_tag = db.query(models.Tag).filter(
                        models.Tag.name == 'Multi-player',
                        models.Tag.type == 'player_mode'
                    ).first()
                    
                    if not multiplayer_tag:
                        multiplayer_tag = models.Tag(name='Multi-player', type='player_mode')
                        db.add(multiplayer_tag)
                        db.flush()
                    
                    # Link game to Multi-player tag
                    existing_link = db.query(models.GameTag).filter(
                        models.GameTag.game_id == new_game.id,
                        models.GameTag.tag_id == multiplayer_tag.id
                    ).first()
                    
                    if not existing_link:
                        game_tag = models.GameTag(game_id=new_game.id, tag_id=multiplayer_tag.id)
                        db.add(game_tag)
                        print(f"   ✓ Auto-linked Massively Multiplayer game to Multi-player tag")
                
                imported_count += 1
                
                # Fetch ALL reviews for newly imported game
                try:
                    from ..services.review_service import review_service
                    print(f"  📊 Fetching ALL reviews for {new_game.title}...")
                    review_result = review_service.fetch_and_store_reviews(
                        db=db,
                        game_id=new_game.id,
                        steam_app_id=int(app_id)
                        # No max_reviews limit - fetch all reviews
                    )
                    if review_result.get("success"):
                        print(f"  ✓ Fetched {review_result.get('new_reviews', 0)} reviews")
                except Exception as review_error:
                    print(f"  ⚠ Failed to fetch reviews: {review_error}")
                
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


@router.post("/steamspy/import/batch/newest")
def import_newest_games_from_steamspy(
    limit: int = Query(50, description="Number of newest games to import", ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Import newest games from SteamSpy into the database
    
    - **limit**: Number of newest games to import (1-500, default: 50)
    
    This will fetch newest games from SteamSpy (sorted by release date), 
    then get detailed info from Steam API, and import them into your database
    """
    try:
        # Get newest games from SteamSpy
        newest_games = SteamAPIClient.get_newest_games_from_steamspy(limit=limit)
        
        if not newest_games:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch newest games from SteamSpy"
            )
        
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        
        for game in newest_games:
            app_id = game.get('app_id')
            
            if not app_id:
                continue
            
            try:
                # Check if game already exists (by title OR steam_app_id)
                existing_game = db.query(models.Game).filter(
                    (models.Game.title == game.get('name')) |
                    (models.Game.steam_app_id == int(app_id))
                ).first()
                
                if existing_game:
                    skipped_count += 1
                    continue
                
                # Fetch detailed info from Steam API (English for reliable date parsing)
                steam_details_en = SteamAPIClient.get_app_details(int(app_id), language="english", country_code="us")
                
                if not steam_details_en:
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
                    # Also fetch Thai version for Thai description (if available)
                    steam_details_th = SteamAPIClient.get_app_details(int(app_id), language="thai", country_code="th")
                    
                    # Import utilities
                    from ..utils.translator import translator
                    from ..utils.text_cleaner import clean_html_text
                    
                    # Try to get Thai description first, fallback to English + translation
                    thai_desc = None
                    english_desc = None
                    
                    # Get English description first
                    about_game_en = steam_details_en.get('about_the_game')
                    short_desc_en = steam_details_en.get('short_description')
                    
                    if about_game_en:
                        english_desc = clean_html_text(about_game_en)
                    elif short_desc_en:
                        english_desc = clean_html_text(short_desc_en)
                    
                    if steam_details_th:
                        # Try Thai about_the_game
                        about_game_th = steam_details_th.get('about_the_game')
                        if about_game_th:
                            cleaned_thai = clean_html_text(about_game_th)
                            # Verify it's actually Thai, not English
                            detected_lang = translator.detect_language(cleaned_thai)
                            if detected_lang == 'th':
                                thai_desc = cleaned_thai
                                print(f"   ✓ Using native Thai description")
                            else:
                                print(f"   ⚠ Steam Thai API returned {detected_lang}, not Thai. Will translate.")
                    
                    # If no Thai description, translate English
                    if not thai_desc and english_desc:
                        thai_desc = translator.translate_to_thai(english_desc)
                        print(f"   ⚡ Translated English description to Thai")
                    
                    # Extract platform info
                    platforms = steam_details_en.get('platforms', {})
                    platform_list = []
                    if platforms.get('windows'): platform_list.append('Windows')
                    if platforms.get('mac'): platform_list.append('Mac')
                    if platforms.get('linux'): platform_list.append('Linux')
                    platform_str = ', '.join(platform_list) if platform_list else None
                    
                    # Extract price info
                    price_overview = steam_details_en.get('price_overview', {})
                    price_str = price_overview.get('final_formatted') if price_overview else None
                    
                    # Extract video URL (first movie)
                    movies = steam_details_en.get('movies', [])
                    video_url = movies[0].get('webm', {}).get('480') if movies else None
                    if not video_url and movies:
                        video_url = movies[0].get('mp4', {}).get('480')
                    
                    # Parse release date (from English API for reliable parsing)
                    release_date_info = steam_details_en.get('release_date', {})
                    release_date_str = release_date_info.get('date')
                    coming_soon = release_date_info.get('coming_soon', False)
                    
                    # Debug: Print raw release date info
                    print(f"🔍 Game: {steam_details_en.get('name')}")
                    print(f"   Release date info: {release_date_info}")
                    print(f"   Date string: '{release_date_str}'")
                    print(f"   Coming soon: {coming_soon}")
                    
                    release_date_obj = None
                    if release_date_str and not coming_soon:
                        try:
                            from datetime import datetime
                            # Try different date formats that Steam uses
                            date_formats = [
                                '%d %b, %Y',      # "9 Jul, 2013"
                                '%b %d, %Y',      # "Jul 9, 2013"
                                '%d %B, %Y',      # "9 July, 2013"
                                '%B %d, %Y',      # "July 9, 2013"
                                '%Y-%m-%d',       # "2013-07-09"
                                '%d %b %Y',       # "9 Jul 2013" (without comma)
                                '%b %d %Y',       # "Jul 9 2013" (without comma)
                                '%Y',             # "2013" (year only)
                            ]
                            
                            for fmt in date_formats:
                                try:
                                    release_date_obj = datetime.strptime(release_date_str, fmt).date()
                                    print(f"   ✓ Parsed date '{release_date_str}' using format '{fmt}' -> {release_date_obj}")
                                    break
                                except ValueError:
                                    continue
                            
                            if not release_date_obj:
                                print(f"   ⚠ Failed to parse date: '{release_date_str}'")
                        except Exception as e:
                            print(f"   ⚠ Error parsing date '{release_date_str}': {e}")
                            pass
                    elif coming_soon:
                        print(f"   ⏳ Game is coming soon, skipping date")
                    else:
                        print(f"   ⚠ No release date string found")
                    
                    # Use Steam API data (English in description, Thai in about_game_th)
                    new_game = models.Game(
                        title=steam_details_en.get('name'),
                        description=english_desc,  # English description
                        about_game_th=thai_desc,   # Thai description (native or translated)
                        genre=", ".join([g["description"] for g in steam_details_en.get("genres", [])[:3]]),
                        image_url=steam_details_en.get('header_image'),
                        release_date=release_date_obj,
                        developer=", ".join(steam_details_en.get('developers', [])),
                        publisher=", ".join(steam_details_en.get('publishers', [])),
                        platform=platform_str,
                        price=price_str,
                        video=video_url,
                        steam_app_id=int(app_id)  # Store Steam App ID
                    )
                
                db.add(new_game)
                db.flush()  # Get the game ID
                
                # Extract and create player mode tags from categories
                categories = steam_details_en.get('categories', [])
                player_mode_tags = []
                
                for category in categories:
                    category_id = category.get('id')
                    # Single-player: category 2
                    # Multi-player: category 1
                    # Co-op: category 9, 24, 36, 37, 38
                    if category_id == 2:
                        player_mode_tags.append('Single-player')
                    elif category_id == 1:
                        player_mode_tags.append('Multi-player')
                    elif category_id in [9, 24, 36, 37, 38]:  # Various co-op modes
                        if 'Co-op' not in player_mode_tags:
                            player_mode_tags.append('Co-op')
                
                # Create/link player mode tags
                for mode_name in player_mode_tags:
                    # Check if tag exists
                    tag = db.query(models.Tag).filter(
                        models.Tag.name == mode_name,
                        models.Tag.type == 'player_mode'
                    ).first()
                    
                    if not tag:
                        tag = models.Tag(name=mode_name, type='player_mode')
                        db.add(tag)
                        db.flush()
                    
                    # Link game to tag
                    existing_link = db.query(models.GameTag).filter(
                        models.GameTag.game_id == new_game.id,
                        models.GameTag.tag_id == tag.id
                    ).first()
                    
                    if not existing_link:
                        game_tag = models.GameTag(game_id=new_game.id, tag_id=tag.id)
                        db.add(game_tag)
                
                # Auto-link Massively Multiplayer games to Multi-player tag
                genres = steam_details_en.get('genres', [])
                is_massively_multiplayer = any(g.get('description') == 'Massively Multiplayer' for g in genres)
                
                if is_massively_multiplayer and 'Multi-player' not in player_mode_tags:
                    # Find or create Multi-player tag
                    multiplayer_tag = db.query(models.Tag).filter(
                        models.Tag.name == 'Multi-player',
                        models.Tag.type == 'player_mode'
                    ).first()
                    
                    if not multiplayer_tag:
                        multiplayer_tag = models.Tag(name='Multi-player', type='player_mode')
                        db.add(multiplayer_tag)
                        db.flush()
                    
                    # Link game to Multi-player tag
                    existing_link = db.query(models.GameTag).filter(
                        models.GameTag.game_id == new_game.id,
                        models.GameTag.tag_id == multiplayer_tag.id
                    ).first()
                    
                    if not existing_link:
                        game_tag = models.GameTag(game_id=new_game.id, tag_id=multiplayer_tag.id)
                        db.add(game_tag)
                        print(f"   ✓ Auto-linked Massively Multiplayer game to Multi-player tag")
                
                imported_count += 1
                
                # Fetch ALL reviews for newly imported game
                try:
                    from ..services.review_service import review_service
                    print(f"  📊 Fetching ALL reviews for {new_game.title}...")
                    review_result = review_service.fetch_and_store_reviews(
                        db=db,
                        game_id=new_game.id,
                        steam_app_id=int(app_id)
                        # No max_reviews limit - fetch all reviews
                    )
                    if review_result.get("success"):
                        print(f"  ✓ Fetched {review_result.get('new_reviews', 0)} reviews")
                except Exception as review_error:
                    print(f"  ⚠ Failed to fetch reviews: {review_error}")
                
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
            "message": f"Batch import of newest games completed",
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


@router.post("/steamspy/update-app-ids")
def update_steam_app_ids(
    limit: int = Query(100, description="Number of games to update", ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Update steam_app_id for existing games by matching title with SteamSpy
    
    This is useful for games imported before steam_app_id column was added.
    """
    try:
        # Get games without steam_app_id
        games_without_appid = db.query(models.Game).filter(
            models.Game.steam_app_id.is_(None)
        ).limit(limit).all()
        
        if not games_without_appid:
            return {
                "success": True,
                "message": "All games already have steam_app_id",
                "updated": 0
            }
        
        # Get all games from SteamSpy
        print(f"📥 Fetching game list from SteamSpy...")
        steamspy_data = SteamAPIClient.get_all_games_from_steamspy()
        
        if not steamspy_data:
            return {
                "success": False,
                "message": "Failed to fetch data from SteamSpy",
                "updated": 0
            }
        
        # Create a mapping of game names to app_ids
        name_to_appid = {}
        for app_id, game_data in steamspy_data.items():
            game_name = game_data.get('name', '').strip().lower()
            if game_name:
                name_to_appid[game_name] = app_id
        
        updated_count = 0
        not_found_count = 0
        
        for game in games_without_appid:
            game_name_lower = game.title.strip().lower()
            
            # Try exact match first
            if game_name_lower in name_to_appid:
                game.steam_app_id = name_to_appid[game_name_lower]
                updated_count += 1
                print(f"   ✓ Updated {game.title} -> App ID: {game.steam_app_id}")
            else:
                not_found_count += 1
                print(f"   ✗ Not found: {game.title}")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Updated {updated_count} games with steam_app_id",
            "updated": updated_count,
            "not_found": not_found_count,
            "total_processed": updated_count + not_found_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating steam_app_ids: {str(e)}"
        )


@router.post("/update-player-modes")
def update_existing_games_with_player_modes(
    limit: int = Query(default=100, description="Maximum number of games to update"),
    db: Session = Depends(get_db)
):
    """
    Update existing games with player mode tags by fetching categories from Steam API.
    
    This endpoint:
    1. Gets games that have steam_app_id
    2. Fetches categories from Steam API
    3. Creates player mode tags (Single-player, Multi-player, Co-op)
    4. Links games to player mode tags
    """
    try:
        import time
        
        # Get games with steam_app_id
        games = db.query(models.Game).filter(
            models.Game.steam_app_id.isnot(None)
        ).limit(limit).all()
        
        if not games:
            return {
                "success": False,
                "message": "No games found with steam_app_id",
                "updated": 0
            }
        
        updated_count = 0
        failed_count = 0
        
        print(f"๐” Updating {len(games)} games with player mode tags...")
        
        for game in games:
            try:
                # Fetch Steam API details
                steam_details = SteamAPIClient.get_app_details(game.steam_app_id)
                
                if not steam_details:
                    print(f"โ  Could not fetch details for {game.title} (App ID: {game.steam_app_id})")
                    failed_count += 1
                    continue
                
                # Extract categories
                categories = steam_details.get('categories', [])
                player_mode_tags = []
                
                for category in categories:
                    category_id = category.get('id')
                    # Single-player: category 2
                    # Multi-player: category 1
                    # Co-op: category 9, 24, 36, 37, 38
                    if category_id == 2:
                        player_mode_tags.append('Single-player')
                    elif category_id == 1:
                        player_mode_tags.append('Multi-player')
                    elif category_id in [9, 24, 36, 37, 38]:  # Various co-op modes
                        if 'Co-op' not in player_mode_tags:
                            player_mode_tags.append('Co-op')
                
                # Create/link player mode tags
                for mode_name in player_mode_tags:
                    # Check if tag exists
                    tag = db.query(models.Tag).filter(
                        models.Tag.name == mode_name,
                        models.Tag.type == 'player_mode'
                    ).first()
                    
                    if not tag:
                        tag = models.Tag(name=mode_name, type='player_mode')
                        db.add(tag)
                        db.flush()
                    
                    # Check if link already exists
                    existing_link = db.query(models.GameTag).filter(
                        models.GameTag.game_id == game.id,
                        models.GameTag.tag_id == tag.id
                    ).first()
                    
                    if not existing_link:
                        game_tag = models.GameTag(game_id=game.id, tag_id=tag.id)
                        db.add(game_tag)
                
                # Auto-link Massively Multiplayer games to Multi-player tag
                genres = steam_details.get('genres', [])
                is_massively_multiplayer = any(g.get('description') == 'Massively Multiplayer' for g in genres)
                
                if is_massively_multiplayer and 'Multi-player' not in player_mode_tags:
                    # Find or create Multi-player tag
                    multiplayer_tag = db.query(models.Tag).filter(
                        models.Tag.name == 'Multi-player',
                        models.Tag.type == 'player_mode'
                    ).first()
                    
                    if not multiplayer_tag:
                        multiplayer_tag = models.Tag(name='Multi-player', type='player_mode')
                        db.add(multiplayer_tag)
                        db.flush()
                    
                    # Link game to Multi-player tag
                    existing_link = db.query(models.GameTag).filter(
                        models.GameTag.game_id == game.id,
                        models.GameTag.tag_id == multiplayer_tag.id
                    ).first()
                    
                    if not existing_link:
                        game_tag = models.GameTag(game_id=game.id, tag_id=multiplayer_tag.id)
                        db.add(game_tag)
                        print(f"   ✓ Auto-linked Massively Multiplayer game to Multi-player tag")

                
                updated_count += 1
                print(f"โ“ Updated {game.title} with {len(player_mode_tags)} player modes")
                
                # Commit every 10 games
                if updated_count % 10 == 0:
                    db.commit()
                    print(f"๐’พ Committed {updated_count} games...")
                
                # Be nice to Steam API
                time.sleep(1.5)
                
            except Exception as e:
                print(f"โ Error updating {game.title}: {e}")
                failed_count += 1
                continue
        
        # Final commit
        db.commit()
        
        return {
            "success": True,
            "message": f"Updated {updated_count} games with player mode tags",
            "updated": updated_count,
            "failed": failed_count,
            "total_processed": len(games)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating player modes: {str(e)}"
        )
@router.post("/link-mm-to-multiplayer")
def link_massively_multiplayer_to_multiplayer(db: Session = Depends(get_db)):
    """
    Link all games with 'Massively Multiplayer' genre to 'Multi-player' player mode tag.
    
    This is useful because Massively Multiplayer games are inherently multiplayer games,
    so they should appear in the Multi-player filter.
    """
    try:
        # Find Massively Multiplayer genre tag
        mm_genre_tag = db.query(models.Tag).filter(
            models.Tag.name == 'Massively Multiplayer',
            models.Tag.type == 'genre'
        ).first()
        
        if not mm_genre_tag:
            return {
                "success": False,
                "message": "Massively Multiplayer genre tag not found"
            }
        
        # Find or create Multi-player tag
        multiplayer_tag = db.query(models.Tag).filter(
            models.Tag.name == 'Multi-player',
            models.Tag.type == 'player_mode'
        ).first()
        
        if not multiplayer_tag:
            multiplayer_tag = models.Tag(name='Multi-player', type='player_mode')
            db.add(multiplayer_tag)
            db.flush()
        
        # Find all games with Massively Multiplayer genre
        mm_game_tags = db.query(models.GameTag).filter(
            models.GameTag.tag_id == mm_genre_tag.id
        ).all()
        
        linked_count = 0
        already_linked_count = 0
        
        for game_tag in mm_game_tags:
            game_id = game_tag.game_id
            
            # Check if already linked to Multi-player
            existing_link = db.query(models.GameTag).filter(
                models.GameTag.game_id == game_id,
                models.GameTag.tag_id == multiplayer_tag.id
            ).first()
            
            if existing_link:
                already_linked_count += 1
            else:
                # Create link
                new_link = models.GameTag(
                    game_id=game_id,
                    tag_id=multiplayer_tag.id
                )
                db.add(new_link)
                linked_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Linked {linked_count} Massively Multiplayer games to Multi-player tag",
            "newly_linked": linked_count,
            "already_linked": already_linked_count,
            "total_mm_games": len(mm_game_tags)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error linking tags: {str(e)}"
        )

