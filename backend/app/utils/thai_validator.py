from typing import List
import re

def is_valid_thai_content(text: str, min_thai_chars: int = 5) -> bool:
    """
    Validates if the content contains enough Thai characters to be considered a Thai review.
    
    Rules:
    1. Must contain at least `min_thai_chars` Thai characters (default 5).
    2. Allows mixed English/Thai content as long as the Thai part meets the threshold.
    3. Filters out pure English content (0 Thai chars).
    4. Filters out very short Thai noise (e.g. "ดี", "dddd", "สนุก").
    
    Args:
        text: The text content to validate
        min_thai_chars: Minimum number of Thai characters required
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not text:
        return False
        
    # Unicode range for Thai: \u0E00-\u0E7F
    thai_chars = len([c for c in text if '\u0E00' <= c <= '\u0E7F'])
    
    if thai_chars > min_thai_chars:
        return True
        
    return False
