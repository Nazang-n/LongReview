import re
import html
from typing import List, Optional

# Comprehensive list of Thai profanities and common variations
THAI_PROFANITY_LIST = [
    "เหี้ย", "ควย", "เย็ด", "มึง", "กู", "สัส", "อีดอก", "จัญไร", "ระยำ", "ควาย", "สตอ", "หน้าม้า", 
    "กระหรี่", "โสเภณี", "สถุน", "ระยำ", "ชิบหาย", "แม่ง", "พ่อง", "แม่ม", "กาก", "สัด", "ไอ้", "อิดอก",
    "ห่า", "ส้นตีน", "ส้นเท้า", "หัวดอ", "กระดอ", "เงี่ยน", "หี", "แตด", "เยส", "คาดอ", "ชักว่าว",
    "หำ", "ตูด", "เยี่ยว", "ขี้", "ฉิบหาย", "ตอแหล", "หน้าด้าน", "ถ่อย", "เลว", "ทราม", "บ้า", "สาด", "แดก"
]

class ReviewFilter:
    """Utility class for cleaning, censoring, and filtering Steam reviews."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Remove BBCode, HTML, and normalize whitespace.
        """
        if not text:
            return ""
        
        # 1. Decode HTML entities
        text = html.unescape(text)
        
        # 2. Remove BBCode tags
        # Replace block tags with newline/space to prevent merging words
        text = re.sub(r'\[/?(h1|h2|h3|hr|list|n)\s*\]', '\n', text, flags=re.IGNORECASE)
        # Remove all other tags
        text = re.sub(r'\[/?[a-zA-Z0-9=*"'':\./\s_\-]+\]', '', text)
        
        # 3. Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # 4. Normalize whitespace
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with single or double newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()

    @staticmethod
    def censor_profanity(text: str) -> str:
        """
        Replace Thai profanities with ***.
        """
        if not text:
            return ""
            
        censored_text = text
        for word in THAI_PROFANITY_LIST:
            # Use regex to match the word (simple boundary check isn't great for Thai, but we do our best)
            # Thai doesn't use spaces, so we just replace the characters
            censored_text = censored_text.replace(word, "***")
            
        return censored_text

    @staticmethod
    def is_spam(text: str) -> bool:
        """
        Check if the text is likely spam (repetitive characters).
        """
        if not text:
            return True
            
        # Check for long sequences of same character (e.g., "5555555555", "aaaaaaaaaa")
        if re.search(r'(.)\1{9,}', text):
            return True
            
        # Check for very short reviews (less than 5 meaningful characters)
        meaningful_chars = re.sub(r'[\s\.\!\?\(\)\[\]\{\}\-\=\+\_\*\&\^\%\$\#\@\~\/\\\|]', '', text)
        if len(meaningful_chars) < 5:
            return True
            
        return False

    @staticmethod
    def get_thai_ratio(text: str) -> float:
        """
        Calculate the ratio of Thai characters to total letters.
        """
        if not text:
            return 0.0
            
        thai_chars = sum(1 for c in text if '\u0e00' <= c <= '\u0e7f')
        letters = sum(1 for c in text if c.isalpha())
        
        if letters == 0:
            return 0.0
            
        return thai_chars / letters

    @classmethod
    def process_review(cls, text: str, is_thai_target: bool = True) -> Optional[str]:
        """
        Main entry point to clean, censor, and filter a review.
        Returns cleaned text if it passes quality filter, else returns None.
        """
        if not text:
            return None
            
        # 1. Clean formatting (BBCode, HTML)
        cleaned = cls.clean_text(text)
        
        # 2. Check for spam/short content
        if cls.is_spam(cleaned):
            return None
            
        # 3. If it's supposed to be a Thai review, check Thai ratio
        if is_thai_target:
            if cls.get_thai_ratio(cleaned) < 0.2: # At least 20% Thai characters
                # If it's mostly English but we wanted Thai, maybe it's not a "Thai review"
                # but we'll accept it if it contains at least some Thai characters (minimum count)
                thai_count = sum(1 for c in cleaned if '\u0e00' <= c <= '\u0e7f')
                if thai_count < 10:
                    return None
        
        # 4. Censor profanity
        final_text = cls.censor_profanity(cleaned)
        
        return final_text
