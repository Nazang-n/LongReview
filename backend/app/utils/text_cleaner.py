"""HTML text cleaning utilities"""
import re
import html


def clean_html_text(html_text: str) -> str:
    """
    Clean HTML text by removing tags and converting to plain text
    
    Args:
        html_text: HTML string with tags
        
    Returns:
        Clean plain text string
    """
    if not html_text:
        return ""
    
    # Decode HTML entities (e.g., &quot; -> ")
    text = html.unescape(html_text)
    
    # Remove <br>, <br/>, <br /> tags and replace with newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline (paragraph break)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove empty lines at start and end
    text = text.strip()
    
    return text


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    # Try to truncate at sentence boundary
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    last_space = truncated.rfind(' ')
    
    if last_period > max_length * 0.7:  # If period is in last 30%
        return text[:last_period + 1]
    elif last_space > max_length * 0.8:  # If space is in last 20%
        return truncated[:last_space] + suffix
    else:
        return truncated + suffix
