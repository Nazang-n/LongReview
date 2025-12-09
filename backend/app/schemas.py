from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Game Schemas
class GameBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    genre: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=10)
    image_url: Optional[str] = None
    release_date: Optional[str] = None
    developer: Optional[str] = None
    publisher: Optional[str] = None


class GameCreate(GameBase):
    pass


class GameUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    genre: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=10)
    image_url: Optional[str] = None
    release_date: Optional[str] = None
    developer: Optional[str] = None
    publisher: Optional[str] = None


class Game(GameBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Review Schemas
class ReviewBase(BaseModel):
    game_id: int
    title: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=10)
    rating: float = Field(..., ge=0, le=10)


class ReviewCreate(ReviewBase):
    user_id: int


class ReviewUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, min_length=10)
    rating: Optional[float] = Field(None, ge=0, le=10)


class Review(ReviewBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
