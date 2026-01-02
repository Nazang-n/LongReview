from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import bcrypt
from .. import models
from ..database import get_db

router = APIRouter(
    prefix="/api/profile",
    tags=["profile"]
)


# Pydantic models
class ProfileUpdate(BaseModel):
    """Request body for updating profile"""
    username: str
    email: EmailStr


class AvatarUpdate(BaseModel):
    """Request body for updating avatar"""
    avatar_url: str  # Base64 encoded image


class PasswordChange(BaseModel):
    """Request body for changing password"""
    current_password: str
    new_password: str


class UserProfileResponse(BaseModel):
    """Response model for user profile"""
    id: int
    username: str
    email: str
    user_role: str
    avatar_url: Optional[str]
    created_at: str


class UserStatsResponse(BaseModel):
    """Response model for user statistics"""
    total_comments: int
    favorites: int


class UserCommentResponse(BaseModel):
    """Response model for user comment with game info"""
    id: int
    game_id: int
    game_title: str
    game_image: Optional[str]
    content: str
    is_edited: bool
    created_at: str
    updated_at: str
    upvotes: int


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    """Get user profile data"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "user_role": user.user_role,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.put("/{user_id}")
def update_profile(
    user_id: int,
    profile: ProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update user profile (username and email)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if username is already taken by another user
    if profile.username != user.username:
        existing_user = db.query(models.User).filter(
            and_(
                models.User.username == profile.username,
                models.User.id != user_id
            )
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Check if email is already taken by another user
    if profile.email != user.email:
        existing_email = db.query(models.User).filter(
            and_(
                models.User.email == profile.email,
                models.User.id != user_id
            )
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
    
    # Update profile
    user.username = profile.username
    user.email = profile.email
    
    db.commit()
    
    return {
        "success": True,
        "message": "Profile updated successfully"
    }


@router.post("/{user_id}/avatar")
def update_avatar(
    user_id: int,
    avatar: AvatarUpdate,
    db: Session = Depends(get_db)
):
    """Update user avatar"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.avatar_url = avatar.avatar_url
    db.commit()
    
    return {
        "success": True,
        "message": "Avatar updated successfully",
        "avatar_url": user.avatar_url
    }


@router.put("/{user_id}/password")
def change_password(
    user_id: int,
    password_data: PasswordChange,
    db: Session = Depends(get_db)
):
    """Change user password"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not bcrypt.checkpw(password_data.current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    hashed_password = bcrypt.hashpw(password_data.new_password.encode('utf-8'), bcrypt.gensalt())
    user.password_hash = hashed_password.decode('utf-8')
    
    db.commit()
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }


@router.get("/{user_id}/comments", response_model=list[UserCommentResponse])
def get_user_comments(user_id: int, db: Session = Depends(get_db)):
    """Get all comments by user with game information"""
    comments = db.query(models.Comment).filter(
        models.Comment.user_id == user_id
    ).order_by(models.Comment.created_at.desc()).all()
    
    result = []
    for comment in comments:
        # Get game info
        game = db.query(models.Game).filter(models.Game.id == comment.game_id).first()
        
        result.append({
            "id": comment.id,
            "game_id": comment.game_id,
            "game_title": game.title if game else "Unknown Game",
            "game_image": game.image_url if game else None,
            "content": comment.content,
            "is_edited": comment.is_edited,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
            "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            "upvotes": comment.upvotes
        })
    
    return result


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """Get user statistics"""
    # Count total comments
    total_comments = db.query(models.Comment).filter(
        models.Comment.user_id == user_id
    ).count()
    
    # Count favorites
    favorites = db.query(models.Favorite).filter(
        models.Favorite.user_id == user_id
    ).count()
    
    return {
        "total_comments": total_comments,
        "favorites": favorites
    }
