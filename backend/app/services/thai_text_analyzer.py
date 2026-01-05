"""
Thai Text Analyzer Service
Uses PyThaiNLP for word tokenization and frequency analysis
"""
from typing import List, Dict, Tuple
from collections import Counter
from pythainlp import word_tokenize
from pythainlp.corpus import thai_stopwords
from pythainlp.tag import pos_tag
import re


class ThaiTextAnalyzer:
    """Analyzes Thai text to extract frequently mentioned words and phrases"""
    
    def __init__(self):
        # Load Thai stopwords
        self.stopwords = set(thai_stopwords())
        
        # Add comprehensive custom stopwords for game reviews
        self.custom_stopwords = {
            # Basic Thai particles and connectors
            'เกม', 'เล่น', 'ครับ', 'ค่ะ', 'นะ', 'จ้า', 'อ่ะ', 'เอ่อ',
            'แล้ว', 'ก็', 'ไป', 'มา', 'ได้', 'ให้', 'ของ', 'ที่', 'ใน', 'กับ',
            'จะ', 'เป็น', 'มี', 'จาก', 'ถึง', 'ว่า', 'อยู่', 'ไว้', 'เอา', 'ถูก',
            'ต้อง', 'ควร', 'อาจ', 'จน', 'เพื่อ', 'แต่', 'หรือ', 'และ',
            
            # Pronouns
            'ผม', 'ฉัน', 'เรา', 'คุณ', 'เขา', 'เธอ', 'มัน', 'ตัว', 'พวก',
            
            # Common adjectives and adverbs (ไม่ต้องการ)
            'ดี', 'เยี่ยม', 'แย่', 'โอเค', 'สนุก', 'ชอบ', 'ชอบมาก', 'เพลิน',
            'โคตร', 'โคตรดี', 'สุด', 'สุดยอด', 'เจ๋ง', 'แรง', 'เห็ด',
            'แนว', 'แนะนำ', 'คิดว่า', 'เหอะ', 'น่า', 'ค่อนข้าง',
            'ok', 'okay', 'nice', 'cool',
            
            # Filler words
            'มาก', 'น้อย', 'เกิน', 'ใหม่', 'เก่า', 'นี่', 'นั่น', 'นี้', 'นั้น',
            'ซะ', 'ซะที', 'สิ', 'จัง', 'เนอะ', 'เลย', 'อะ', 'จ๊ะ', 'จ้ะ',
            'บ้าง', 'หรอก', 'เหรอ', 'หรอ', 'ไหม', 'มั้ย', 'รึ',
            
            # Incomplete words from tokenization errors
            'เก', 'เล่', 'เกม', 'ซอม', 'ซ่อม', 'สร้าง', 'กรรจ', 'กรร',
            'มอน', 'โปเกมอน',  # คำตัดไม่สมบูรณ์
            
            # Common nouns ที่ไม่มีประโยชน์
            'ตัว', 'อัน', 'คน', 'ครั้ง', 'ช่วง', 'ระดับ', 'เวลา',
            
            # Common expressions
            'wowwow', 'wow', 'haha', 'lol', 'omg', 'wtf',
            
            # English stopwords and common words
            'steam', 'game', 'play', 'playing', 'played', 'good', 'ok', 'not',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'has', 'have', 'had',
            'in', 'on', 'at', 'to', 'for', 'with', 'and', 'or', 'but',
            'this', 'that', 'very', 'really', 'so', 'too', 'much', 'many',
            'some', 'any', 'all', 'can', 'will', 'would', 'could', 'should',
            'funny', 'nice', 'best', 'worst', 'better', 'great'
        }
        self.stopwords.update(self.custom_stopwords)
    
    def is_thai_text(self, text: str, min_thai_ratio: float = 0.3) -> bool:
        """
        Check if text contains enough Thai characters
        
        Args:
            text: Text to check
            min_thai_ratio: Minimum ratio of Thai characters (default 0.3 = 30%)
            
        Returns:
            True if text has enough Thai content, False otherwise
        """
        if not text:
            return False
        
        # Count Thai characters
        thai_chars = sum(1 for c in text if '\u0e00' <= c <= '\u0e7f')
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return False
        
        thai_ratio = thai_chars / total_chars
        return thai_ratio >= min_thai_ratio
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text by reducing repeated characters
        e.g., 'gooddddd' -> 'good', 'สนุกกกก' -> 'สนุก'
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return text
        
        # Reduce 3+ repeated characters to 2
        # e.g., 'goooood' -> 'good', 'สนุกกกก' -> 'สนุก'
        normalized = re.sub(r'(.)\1{2,}', r'\1', text)
        return normalized
    
    def tokenize_and_filter(self, text: str, use_pos_tagging: bool = True) -> List[str]:
        """
        Tokenize Thai text and filter to extract only meaningful nouns
        
        Args:
            text: Thai text to analyze
            use_pos_tagging: If True, use POS tagging to extract only nouns
            
        Returns:
            List of filtered words (nouns if use_pos_tagging=True)
        """
        if not text:
            return []
        
        # Tokenize using newmm engine (best for Thai)
        words = word_tokenize(text, engine='newmm')
        
        # Apply POS tagging if requested
        if use_pos_tagging:
            # Get POS tags
            pos_tagged = pos_tag(words, engine='perceptron', corpus='orchid_ud')
            
            # Filter for nouns only (NOUN, PROPN)
            # NOUN = common nouns (มอนสเตอร์, คราฟ, สัตว์)
            # PROPN = proper nouns (Palworld, GTA)
            filtered_words = []
            for word, pos in pos_tagged:
                word = word.strip().lower()
                
                # Normalize repeated characters
                word = self.normalize_text(word)
                
                # Keep only nouns that are:
                # - Tagged as NOUN or PROPN
                # - At least 3 characters long
                # - Not in stopwords
                # - Alphanumeric
                is_thai = any('\u0e00' <= c <= '\u0e7f' for c in word)
                is_meaningful_english = word.isalpha() and not is_thai and len(word) >= 5
                
                if (pos in ['NOUN', 'PROPN'] and
                    len(word) >= 3 and
                    word not in self.stopwords and
                    word.isalpha() and
                    (is_thai or is_meaningful_english)):
                    filtered_words.append(word)
        else:
            # Original filtering without POS tagging
            filtered_words = []
            for word in words:
                word = word.strip().lower()
                
                # Normalize repeated characters
                word = self.normalize_text(word)
                
                is_thai = any('\u0e00' <= c <= '\u0e7f' for c in word)
                is_meaningful_english = word.isalpha() and not is_thai and len(word) >= 5
                
                if (len(word) >= 3 and 
                    word not in self.stopwords and 
                    not word.isspace() and
                    word.isalpha() and
                    (is_thai or is_meaningful_english)):
                    filtered_words.append(word)
        
        return filtered_words
    
    def extract_ngrams(self, words: List[str], n: int = 2) -> List[str]:
        """
        Extract n-grams from a list of words
        
        Args:
            words: List of words
            n: Size of n-gram (2 for bigrams, 3 for trigrams)
            
        Returns:
            List of n-grams joined by underscore
        """
        if len(words) < n:
            return []
        
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = '_'.join(words[i:i+n])
            ngrams.append(ngram)
        
        return ngrams
    
    def analyze_texts(self, texts: List[str], top_n: int = 10, include_ngrams: bool = True, use_pos_tagging: bool = True) -> List[Dict[str, any]]:
        """
        Analyze multiple texts and return top N most frequent words and phrases
        
        Args:
            texts: List of Thai texts to analyze
            top_n: Number of top words to return
            include_ngrams: Whether to include bigrams and trigrams
            use_pos_tagging: Whether to use POS tagging to extract only nouns
            
        Returns:
            List of dicts with 'word' and 'count' keys, sorted by count descending
        """
        all_terms = []
        
        # Tokenize and filter all texts
        for text in texts:
            words = self.tokenize_and_filter(text, use_pos_tagging=use_pos_tagging)
            
            # Add individual words
            all_terms.extend(words)
            
            # Add n-grams if requested
            if include_ngrams:
                # Add bigrams (2-word phrases)
                bigrams = self.extract_ngrams(words, n=2)
                all_terms.extend(bigrams)
                
                # Add trigrams (3-word phrases)
                trigrams = self.extract_ngrams(words, n=3)
                all_terms.extend(trigrams)
        
        # Count term frequencies
        term_counts = Counter(all_terms)
        
        # Get top N terms
        top_terms = term_counts.most_common(top_n)
        
        # Format result
        result = [
            {'word': term, 'count': count}
            for term, count in top_terms
        ]
        
        return result
    
    def analyze_reviews_by_sentiment(
        self, 
        positive_reviews: List[str], 
        negative_reviews: List[str],
        top_n: int = 10,
        include_ngrams: bool = True,
        use_pos_tagging: bool = True,
        filter_thai_only: bool = True
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Analyze reviews separated by sentiment
        
        Args:
            positive_reviews: List of positive review texts
            negative_reviews: List of negative review texts
            top_n: Number of top words to return for each sentiment
            include_ngrams: Whether to include bigrams and trigrams
            use_pos_tagging: Whether to use POS tagging to extract only nouns
            filter_thai_only: Whether to filter out non-Thai reviews
            
        Returns:
            Tuple of (positive_tags, negative_tags)
        """
        # Filter for Thai reviews if requested
        if filter_thai_only:
            positive_reviews = [r for r in positive_reviews if self.is_thai_text(r)]
            negative_reviews = [r for r in negative_reviews if self.is_thai_text(r)]
        
        positive_tags = self.analyze_texts(positive_reviews, top_n, include_ngrams, use_pos_tagging)
        negative_tags = self.analyze_texts(negative_reviews, top_n, include_ngrams, use_pos_tagging)
        
        return positive_tags, negative_tags
