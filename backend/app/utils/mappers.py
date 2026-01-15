"""
Data mapping utilities
Provides functions to map external API data to internal formats
"""
from typing import Dict, Any
from app.utils.date_utils import format_thai_date


def clean_description(description: str) -> str:
    """
    Clean description by replacing [...] with ... and removing WordPress footer
    
    Args:
        description: Raw description text
        
    Returns:
        Cleaned description text
    """
    if not description:
        return "ไม่มีคำอธิบาย"
    
    # Replace [...] truncation markers with ...
    cleaned = description.replace("[...]", "...")
    
    # Remove "The post ... appeared first on ..." footer ONLY if it's at the end
    # This pattern appears at the end of WordPress blog excerpts
    # Use a more specific pattern to avoid removing legitimate content
    import re
    # Match "The post <title> appeared first on <site>." at the end
    # Use non-greedy match and require "appeared first on" to avoid false positives
    cleaned = re.sub(r'\s*The post .+? appeared first on .+?\.\s*$', '', cleaned)
    
    # Trim whitespace
    cleaned = cleaned.strip()
    
    return cleaned if cleaned else "ไม่มีคำอธิบาย"


def map_news_item(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map NewsData.io article to internal news format
    
    Args:
        article: Raw article data from NewsData.io API
        
    Returns:
        Mapped news item dictionary
    """
    return {
        "id": article.get("article_id"),
        "title": article.get("title"),
        "description": clean_description(article.get("description")),
        "image": article.get("image_url") or "https://via.placeholder.com/800x400?text=No+Image",
        "link": article.get("link"),
        "date": format_thai_date(article.get("pubDate", "")),
        "author": article.get("source_name")
    }


def map_steam_game(game_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Steam API game data to internal format
    
    Args:
        game_data: Raw game data from Steam API
        
    Returns:
        Mapped game dictionary
    """
    # TODO: Implement Steam game mapping
    return game_data
