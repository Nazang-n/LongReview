from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, Any
from datetime import datetime
import re


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., max_length=100)
    email: str  # Changed from EmailStr to allow custom validation


class UserCreate(BaseModel):
    # Define fields in the order we want them validated
    username: str = Field(..., max_length=100)
    email: str
    password: str = Field(...)
    
    @model_validator(mode='before')
    @classmethod
    def validate_fields_in_order(cls, data: Any) -> Any:
        """Validate fields in specific order: username -> email -> password"""
        if not isinstance(data, dict):
            return data
        
        # 1. Validate username first
        username = data.get('username', '')
        if not username or len(username) < 3:
            raise ValueError('ชื่อผู้ใช้งานต้องมีอย่างน้อย 3 ตัวอักษร')
        
        # 2. Validate email second
        email = data.get('email', '')
        if not email or '@' not in email:
            raise ValueError('รูปแบบอีเมลไม่ถูกต้อง')
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError('รูปแบบอีเมลไม่ถูกต้อง')
        
        # Normalize email
        data['email'] = email.lower()
        
        # 3. Validate password last
        password = data.get('password', '')
        if not password or len(password) < 6:
            raise ValueError('รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร')
        
        return data


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None  # Changed from EmailStr
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 3:
            raise ValueError('ชื่อผู้ใช้งานต้องมีอย่างน้อย 3 ตัวอักษร')
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        # Basic email validation
        if '@' not in v:
            raise ValueError('รูปแบบอีเมลไม่ถูกต้อง')
        
        # More comprehensive email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('รูปแบบอีเมลไม่ถูกต้อง')
        
        return v.lower()


class User(UserBase):
    id: int
    user_role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Game Schemas
class GameBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    genre: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=10)
    image_url: Optional[str] = None
    release_date: Optional[str] = None  # Keep as string for JSON serialization
    developer: Optional[str] = None
    publisher: Optional[str] = None
    platform: Optional[str] = None
    price: Optional[str] = None
    video: Optional[str] = None
    screenshots: Optional[str] = None
    about_game_th: Optional[str] = None
    genre_th: Optional[str] = None
    player_modes: Optional[list[str]] = []


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
    platform: Optional[str] = None
    price: Optional[str] = None
    video: Optional[str] = None
    about_game_th: Optional[str] = None


class Game(GameBase):
    id: int

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
    user_id: Optional[int] = None  # user_id can be null for steam reviews
    steam_id: Optional[str] = None
    is_steam_review: bool = False
    steam_author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
