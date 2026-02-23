from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, Date, text, ForeignKey, BigInteger
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base


class User(Base):
    """User model - maps to existing 'user' table in database"""
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column("user_name", String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column("password", String(255), nullable=False)
    user_role = Column(String(50), nullable=False, default="User")
    avatar_url = Column(Text)  # Store avatar as base64 or URL
    created_at = Column("created_date", DateTime(timezone=True), server_default=func.now())


class Game(Base):
    """Game model - maps to existing 'game' table in database"""
    __tablename__ = "game"  # Table name is 'game' not 'games'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Map to existing database columns
    title = Column("name", Text, nullable=False, index=True)  # DB column: name
    description = Column("info", Text)  # DB column: info
    image_url = Column("picture", Text)  # DB column: picture
    
    # Existing columns in database
    platform = Column(Text)  # Platform (windows, mac, linux)
    price = Column(Text)  # Price from Steam
    video = Column(Text)  # Video URL (can store JSON for multiple videos)
    screenshots = Column(Text)  # Screenshots JSON array
    release_date = Column(Date)  # Release date
    
    # Additional columns for Steam API data (add these to DB if needed)
    genre = Column(String(100))  # Game genres
    developer = Column(String(255))  # Developer name
    publisher = Column(String(255))  # Publisher name
    rating = Column(Float)  # Game rating (optional)
    about_game_th = Column(Text)  # Thai translation of game details
    steam_app_id = Column(Integer, unique=True, index=True)  # Steam App ID from SteamSpy
    last_review_fetch = Column(DateTime(timezone=True), nullable=True)  # Last time reviews were fetched




class Review(Base):
    """Review model for Steam game reviews"""
    __tablename__ = "review"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Existing columns in database
    game_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    owner = Column(String(255))
    
    # Steam review columns
    steam_id = Column(String(255), unique=True, index=True)
    voted_up = Column("voted_up", Boolean)  # Column has trailing space in DB
    created_at = Column("created_at", DateTime(timezone=True))  # Column has trailing space in DB
    
    # New Steam review fields added by migration
    is_steam_review = Column(Boolean, default=False, nullable=False, index=True)
    steam_author = Column(String(255))
    helpful_count = Column(Integer, default=0)
    playtime_hours = Column(Float)



class GameSentiment(Base):
    """Game sentiment cache - stores Steam review sentiment data"""
    __tablename__ = "game_sentiment"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("game.id"), unique=True, nullable=False, index=True)
    positive_percent = Column(Float, nullable=True)
    negative_percent = Column(Float, nullable=True)
    total_reviews = Column(Integer, nullable=True)
    review_score_desc = Column(String(50), nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=True)
    tag_status = Column(String(20), default='pending', nullable=True)  # 'success', 'insufficient', 'no_reviews', 'error'



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


class GameReviewTag(Base):
    """Game review tags - stores analyzed tags from Thai reviews"""
    __tablename__ = "game_review_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, nullable=False, index=True)
    tag_type = Column(String(20), nullable=False)  # 'positive' or 'negative'
    tag_word = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Favorite(Base):
    """Favorite model - tracks user's favorite games"""
    __tablename__ = "favorite"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    game_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ensure a user can only favorite a game once
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )


class Comment(Base):
    """Comment model - user comments on games"""
    __tablename__ = "comment"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_edited = Column(Boolean, default=False, nullable=False)
    upvotes = Column(Integer, default=0, nullable=False)  # Store upvotes directly
    voted_user_ids = Column(Text, default='[]', nullable=False)  # JSON array of user IDs who voted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CommentReport(Base):
    """CommentReport model - user reports for inappropriate comments"""
    __tablename__ = "comment_report"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, nullable=False, index=True)
    reporter_id = Column(Integer, nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default='pending', nullable=False)  # 'pending', 'reviewed', 'dismissed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())



class Tag(Base):
    """Tag model - stores filter tags (genres, platforms, player modes)"""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # 'genre', 'platform', 'player_mode'
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GameTag(Base):
    """GameTag model - links games to tags (many-to-many relationship)"""
    __tablename__ = "game_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, nullable=False, index=True)
    tag_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    """Password Reset Token model - stores verification codes for password reset"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)  # Secure token
    code = Column(String(6), nullable=False)  # 6-digit verification code
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)


class DailyUpdateLog(Base):
    """Daily Update Log - tracks daily automated update operations"""
    __tablename__ = "daily_update_log"
    
    id = Column(Integer, primary_key=True, index=True)
    update_type = Column(String(50), nullable=False, index=True)  # 'news', 'games', 'sentiment', 'tags', 'reviews'
    update_date = Column(Date, nullable=False, index=True)  # Date of the update
    status = Column(String(20), nullable=False)  # 'success', 'partial', 'failed'
    items_processed = Column(Integer, default=0)
    items_successful = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # For tracking incomplete game updates
    game_id = Column(Integer, ForeignKey("game.id"), nullable=True, index=True)  # Specific game if applicable
