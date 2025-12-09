from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """User model - maps to existing 'user' table in database"""
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class Game(Base):
    """Game model for storing game information"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    genre = Column(String(100))
    rating = Column(Float)
    image_url = Column(String(500))
    release_date = Column(String(50))
    developer = Column(String(255))
    publisher = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Review(Base):
    """Review model for game reviews"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255))
    content = Column(Text, nullable=False)
    rating = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
