"""
Application configuration settings
Centralized configuration using Pydantic BaseSettings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # NewsData.io API
    NEWSDATA_API_KEY: str = "pub_5f46a4d4133a4a3fb02a880318ce3cb9"
    NEWSDATA_API_URL: str = "https://newsdata.io/api/1/news"
    NEWSDATA_COUNTRY: str = ""  # Get Thai news from all countries
    NEWSDATA_QUERY: str = "เกม OR gaming OR esports OR อีสปอร์ต OR PlayStation OR Xbox OR Nintendo"
    NEWSDATA_LANGUAGE: str = "th"  # Thai language for Thai users
    
    # Steam API
    STEAM_API_KEY: Optional[str] = None
    STEAM_API_URL: str = "https://api.steampowered.com"
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:4200"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # App Settings
    APP_NAME: str = "LongReview API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Cache Settings
    CACHE_TTL: int = 600  # 10 minutes in seconds (reduced for fresher news)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
