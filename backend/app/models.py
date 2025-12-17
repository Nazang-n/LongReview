from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, Date
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """User model - maps to existing 'user' table in database"""
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column("user_name", String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column("password", String(255), nullable=False)
    user_role = Column(String(50), nullable=False, default="User")
    created_at = Column("created_date", DateTime(timezone=True), server_default=func.now())


class Game(Base):
    """Game model - maps to existing 'game' table in database"""
    __tablename__ = "game"  # Table name is 'game' not 'games'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Map to existing database columns
    title = Column("name", String(255), nullable=False, index=True)  # DB column: name
    description = Column("info", String(255))  # DB column: info
    image_url = Column("picture", String(255))  # DB column: picture
    
    # Existing columns in database
    platform = Column(String(255))  # Platform (windows, mac, linux)
    price = Column(String(255))  # Price from Steam
    video = Column(String(255))  # Video URL
    release_date = Column(Date)  # Release date
    admin_id = Column(Integer)  # Admin ID
    
    # Additional columns for Steam API data (add these to DB if needed)
    genre = Column(String(100))  # Game genres
    developer = Column(String(255))  # Developer name
    publisher = Column(String(255))  # Publisher name
    rating = Column(Float)  # Game rating (optional)


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
