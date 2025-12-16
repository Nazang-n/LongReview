"""
Data mapping utilities
Provides functions to map external API data to internal formats
"""
from typing import Dict, Any
from app.utils.date_utils import format_thai_date


def clean_description(description: str) -> str:
    """
    Clean description by removing truncation markers and handling cut-off text
    
    Args:
        description: Raw description text
        
    Returns:
        Cleaned description text
    """
    if not description:
        return "ไม่มีคำอธิบาย"
    
    # Remove [...] truncation markers
    cleaned = description.replace("[...]", "")
    
    # Remove "The post ... appeared first on ..." footer
    if "The post" in cleaned and "appeared first on" in cleaned:
        cleaned = cleaned.split("The post")[0]
    
    # Trim whitespace
    cleaned = cleaned.strip()
    
    # If text doesn't end with proper punctuation, it's likely truncated
    # Add ellipsis for better readability
    if cleaned and not cleaned[-1] in '.!?。':
        # Check if it's a complete sentence or cut-off
        # If it ends with incomplete word (no space before last char), add ...
        if len(cleaned) > 50:  # Only for reasonably long text
            cleaned = cleaned + "..."
    
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
        "author": article.get("source_name"),
        "category": article.get("category", ["ข่าวสาร"])[0] if article.get("category") else "ข่าวสาร"
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
