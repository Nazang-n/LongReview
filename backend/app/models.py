from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, Date, text
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
    
    # Steam review columns
    steam_id = Column(String(255), unique=True, index=True)
    voted_up = Column("voted_up", Boolean)  # Column has trailing space in DB
    created_at = Column("created_at", DateTime(timezone=True))  # Column has trailing space in DB
    
    # New Steam review fields added by migration
    is_steam_review = Column(Boolean, default=False, nullable=False, index=True)
    steam_author = Column(String(255))
    helpful_count = Column(Integer, default=0)
    playtime_hours = Column(Float)


class AnalyReview(Base):
    """Sentiment analysis - stores only voted_up from Steam reviews"""
    __tablename__ = "analyreview"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, nullable=False, index=True)
    voted_up = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('NOW()'))



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
    tag_count = Column(Integer, nullable=False, default=0)
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CommentVote(Base):
    """CommentVote model - tracks thumbs up/down votes on comments"""
    __tablename__ = "comment_vote"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    vote_type = Column(String(10), nullable=False)  # 'up' or 'down'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ensure a user can only vote once per comment
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )


class CommentReport(Base):
    """CommentReport model - user reports for inappropriate comments"""
    __tablename__ = "comment_report"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, nullable=False, index=True)
    reporter_id = Column(Integer, nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default='pending', nullable=False)  # 'pending', 'reviewed', 'dismissed'
    reviewed_by = Column(Integer)  # Admin user ID who reviewed
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


