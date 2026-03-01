from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from pydantic import BaseModel
from .. import models
from ..database import get_db
from ..routes.games import serialize_game

router = APIRouter(
    prefix="/api/favorites",
    tags=["favorites"]
)


class FavoriteRequest(BaseModel):
    """Request body for adding/removing favorites"""
    user_id: int


class FavoriteResponse(BaseModel):
    """Response for favorite operations"""
    success: bool
    message: str
    is_favorited: bool = False


@router.post("/{game_id}", response_model=FavoriteResponse)
def add_favorite(
    game_id: int,
    request: FavoriteRequest,
    db: Session = Depends(get_db)
):
    """
    Add a game to user's favorites.
    
    - **game_id**: The ID of the game to favorite
    - **user_id**: The ID of the user (from request body)
    """
    # Check if game exists
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found"
        )
    
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {request.user_id} not found"
        )
    
    # Check if already favorited
    existing_favorite = db.query(models.Favorite).filter(
        and_(
            models.Favorite.user_id == request.user_id,
            models.Favorite.game_id == game_id
        )
    ).first()
    
    if existing_favorite:
        return FavoriteResponse(
            success=True,
            message="Game is already in favorites",
            is_favorited=True
        )
    
    # Create new favorite
    new_favorite = models.Favorite(
        user_id=request.user_id,
        game_id=game_id
    )
    
    db.add(new_favorite)
    db.commit()
    
    return FavoriteResponse(
        success=True,
        message="Game added to favorites",
        is_favorited=True
    )


@router.delete("/{game_id}", response_model=FavoriteResponse)
def remove_favorite(
    game_id: int,
    request: FavoriteRequest,
    db: Session = Depends(get_db)
):
    """
    Remove a game from user's favorites.
    
    - **game_id**: The ID of the game to unfavorite
    - **user_id**: The ID of the user (from request body)
    """
    # Find the favorite
    favorite = db.query(models.Favorite).filter(
        and_(
            models.Favorite.user_id == request.user_id,
            models.Favorite.game_id == game_id
        )
    ).first()
    
    if not favorite:
        return FavoriteResponse(
            success=True,
            message="Game was not in favorites",
            is_favorited=False
        )
    
    # Delete the favorite
    db.delete(favorite)
    db.commit()
    
    return FavoriteResponse(
        success=True,
        message="Game removed from favorites",
        is_favorited=False
    )


@router.get("/", response_model=List[dict])
def get_user_favorites(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Get all favorite games for a user.
    
    - **user_id**: The ID of the user (query parameter)
    """
    # Get all favorites for the user
    favorites = db.query(models.Favorite).filter(
        models.Favorite.user_id == user_id
    ).order_by(models.Favorite.created_at.desc()).all()
    
    # Get full game details for each favorite
    favorite_games = []
    for favorite in favorites:
        game = db.query(models.Game).filter(models.Game.id == favorite.game_id).first()
        if game:
            game_dict = serialize_game(game)
            game_dict['favorited_at'] = favorite.created_at.isoformat() if favorite.created_at else None
            favorite_games.append(game_dict)
    
    return favorite_games


@router.get("/check/{game_id}", response_model=FavoriteResponse)
def check_favorite(
    game_id: int,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Check if a game is in user's favorites.
    
    - **game_id**: The ID of the game to check
    - **user_id**: The ID of the user (query parameter)
    """
    favorite = db.query(models.Favorite).filter(
        and_(
            models.Favorite.user_id == user_id,
            models.Favorite.game_id == game_id
        )
    ).first()
    
    is_favorited = favorite is not None
    
    return FavoriteResponse(
        success=True,
        message="Favorite status checked",
        is_favorited=is_favorited
    )
