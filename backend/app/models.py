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
    about_game_th = Column(Text)  # Thai translation of game details
    steam_app_id = Column(String(50), unique=True, index=True)  # Steam App ID from SteamSpy




class Review(Base):
    """Review model for Steam game reviews"""
    __tablename__ = "review"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Existing columns in database
    game_id = Column(Integer, nullable=False, index=True)
    admin_id = Column(Integer)
    content = Column(Text, nullable=False)
    owner = Column(String(255))
    
    # New columns added for Steam reviews
    steam_id = Column(String(255), unique=True, index=True)
    voted_up = Column("voted_up", Boolean)  # Column has trailing space in DB
    created_at = Column("created_at", DateTime(timezone=True))  # Column has trailing space in DB




class News(Base):
    """News model for storing gaming news articles"""
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(String(255), unique=True, nullable=False, index=True)  # NewsData.io article_id
    title = Column(String(500), nullable=False)
    description = Column(Text)
    image_url = Column(String(1000))
    link = Column(String(1000), nullable=False)
    pub_date = Column(DateTime(timezone=True), nullable=False, index=True)  # For sorting
    source_name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # When added to our DB
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # For cleanup
    is_active = Column(Boolean, default=True, nullable=False, index=True)  # Soft delete


