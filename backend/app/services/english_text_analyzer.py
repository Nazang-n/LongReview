
"""
English Text Analyzer
Analyzes English game reviews to extract meaningful phrases and tags
Uses NLTK for POS tagging and phrase extraction
"""
from typing import List, Counter, Dict, Set, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from textblob import TextBlob


class EnglishTextAnalyzer:
    """Analyzer for English text using NLTK"""
    
    def __init__(self):
        """Initialize the analyzer with NLTK and stopwords"""
        # Import NLTK
        try:
            import nltk
            from nltk import pos_tag, word_tokenize
            from nltk.corpus import stopwords
            
            # Store NLTK functions
            self.nltk = nltk
            self.pos_tag = pos_tag
            self.word_tokenize = word_tokenize
            
            # Download required data (silently)
            try:
                nltk.data.find('tokenizers/punkt_tab')
            except LookupError:
                print("[EnglishAnalyzer] Downloading NLTK punkt_tab tokenizer...")
                nltk.download('punkt_tab', quiet=True)
            
            try:
                nltk.data.find('taggers/averaged_perceptron_tagger_eng')
            except LookupError:
                print("[EnglishAnalyzer] Downloading NLTK POS tagger...")
                nltk.download('averaged_perceptron_tagger_eng', quiet=True)
            
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                print("[EnglishAnalyzer] Downloading NLTK stopwords...")
                nltk.download('stopwords', quiet=True)
            
            # Get NLTK stopwords
            self.nltk_stopwords = set(stopwords.words('english'))
            
        except ImportError:
            raise ImportError(
                "NLTK is not installed. Please run: pip install nltk"
            )
        
        # Comprehensive custom stopwords for game reviews
        self.custom_stopwords = {
            # Game-related but too generic
            'game', 'games', 'gaming', 'play', 'playing', 'played', 'player', 'players',
            
            # Generic words
            'thing', 'things', 'stuff', 'lot', 'lots', 'time', 'times',
            'way', 'ways', 'get', 'getting', 'make', 'making', 'made',
            'really', 'pretty', 'quite', 'very', 'much', 'many', 'more', 'most',
            
            # Too vague adjectives ONLY - removed 'great', 'amazing' to allow phrases
            'good', 'bad', 'nice', 'cool', 'ok', 'okay', 'fine',
            'real', 'super', 'fun', 'best',  # too generic
            
            # Negative adjectives (to avoid contradictory trigrams)
            'boring', 'terrible', 'awful', 'horrible', 'poor', 'worse', 'worst',
            'broken', 'buggy', 'unplayable',
            
            # Profanity and slang
            'fuck', 'fucking', 'fuckin', 'fucken', 'fck', 'fking',
            'shit', 'shitty', 'damn', 'damned', 'crap', 'crappy',
            'ass', 'arse', 'bitch', 'hell',
            'asf', 'af',  # abbreviations (as fuck)
            'rn', 'tbh', 'imo', 'imho',  # slang abbreviations
            
            # Common but meaningless
            'still', 'even', 'just', 'like', 'also', 'always', 'never', 'ever',
            'there', 'here', 'where', 'people', 'person', 'everyone',
            
            # Generic nouns
            'year', 'years', 'month', 'months', 'day', 'days',
            'hour', 'hours', 'minute', 'minutes', 'second', 'seconds',
            
            # Common verbs
            'want', 'wanted', 'need', 'needed', 'give', 'giving', 'gave',
            'take', 'taking', 'took', 'come', 'coming', 'came',
            'go', 'going', 'went', 'know', 'knowing', 'knew',
        }
        
        # Combine NLTK and custom stopwords
        self.stopwords = self.nltk_stopwords.union(self.custom_stopwords)
        
        # Meta tags - phrases that talk about the review itself, not the game
        self.meta_tags = {
            'positive review', 'negative review', 'recommend game',
            'writing review', 'bought game', 'playing game',
            'recommend buying', 'highly recommend', 'would recommend',
            'playtime hours', 'hours played', 'time playing',
            'review helpful', 'leave review', 'steam review'
        }
        
        # Generic phrases - vague or user-centric phrases not describing game features
        self.generic_phrases = {
            'little bit', 'current state', 'huge fan', 'big fan',
            'long time', 'first time', 'bad thing', 'good thing',
            'much time', 'many times', 'last year', 'next year',
            'pokemon fan', 'huge pokemon fan', 'fan base',
            'huge pokemon', 'progression feels', 'pokemon company',
            'cant wait'
        }
    
    def extract_phrases(self, text: str) -> List[str]:
        """
        Extract meaningful phrases from English text
        ONLY returns multi-word phrases (2-3 words)
        Supports bigrams and trigrams for more complete phrases
        
        Args:
            text: English text to analyze
            
        Returns:
            List of meaningful phrases (2-3 words only)
        """
        if not text:
            return []
        
        # Lowercase and tokenize
        text = text.lower()
        tokens = self.word_tokenize(text)
        
        # POS tagging
        pos_tagged = self.pos_tag(tokens)
        
        phrases = []
        
        # Extract multi-word patterns (bigrams and trigrams)
        for i in range(len(pos_tagged)):
            word, pos = pos_tagged[i]
            
            # Skip if not a noun
            if pos not in ['NN', 'NNS', 'NNP', 'NNPS']:
                continue
            
            # Skip stopwords
            if word in self.stopwords:
                continue
            
            # Skip very short words
            if len(word) < 3:
                continue
            
            # Skip if not alphabetic
            if not word.isalpha():
                continue
            
            # Try to build trigram first (3 words)
            if i >= 2:
                word1, pos1 = pos_tagged[i-2]
                word2, pos2 = pos_tagged[i-1]
                
                # Check for ADJ + ADJ + NOUN (e.g., "grand theft auto")
                # or ADJ + NOUN + NOUN (e.g., "online multiplayer mode")
                # or NOUN + NOUN + NOUN (e.g., "role playing game")
                if (word1 not in self.stopwords and len(word1) >= 3 and word1.isalpha() and
                    word2 not in self.stopwords and len(word2) >= 3 and word2.isalpha()):
                    
                    is_valid_trigram = False
                    
                    # ADJ + ADJ + NOUN
                    if pos1 in ['JJ', 'JJR', 'JJS'] and pos2 in ['JJ', 'JJR', 'JJS']:
                        is_valid_trigram = True
                    # ADJ + NOUN + NOUN
                    elif pos1 in ['JJ', 'JJR', 'JJS'] and pos2 in ['NN', 'NNS', 'NNP', 'NNPS']:
                        is_valid_trigram = True
                    # NOUN + NOUN + NOUN
                    elif pos1 in ['NN', 'NNS', 'NNP', 'NNPS'] and pos2 in ['NN', 'NNS', 'NNP', 'NNPS']:
                        is_valid_trigram = True
                    
                    if is_valid_trigram:
                        phrase = f"{word1} {word2} {word}"
                        phrases.append(phrase)
                        continue  # Skip bigram check
            
            # Try bigram (2 words) if trigram didn't match
            if i > 0:
                prev_word, prev_pos = pos_tagged[i-1]
                if (prev_word not in self.stopwords and
                    len(prev_word) >= 3 and
                    prev_word.isalpha()):
                    
                    # ADJ + NOUN or NOUN + NOUN
                    if prev_pos in ['JJ', 'JJR', 'JJS', 'NN', 'NNS', 'NNP', 'NNPS']:
                        phrase = f"{prev_word} {word}"
                        phrases.append(phrase)
        
        return phrases
    
    def _normalize_word(self, word: str) -> str:
        """
        Simple normalization to handle plural forms
        
        Args:
            word: Word to normalize
            
        Returns:
            Normalized word (singular form)
        """
        # Simple plural handling
        if word.endswith('ies') and len(word) > 4:
            return word[:-3] + 'y'  # cities -> city
        elif word.endswith('ses') and len(word) > 4:
            #bases → base (just remove 's')
            return word[:-1]  # bases -> base
        elif word.endswith('es') and len(word) > 3:
            return word[:-2]  # boxes -> box
        elif word.endswith('s') and len(word) > 2:
            return word[:-1]  # pals -> pal, updates -> update
        return word
    
    def analyze_texts(self, texts: List[str], top_n: int = 10, min_count: int = 3, game_name: str = None, min_count_ratio: float = 0.1) -> List[Dict[str, any]]:
        """
        Analyze multiple texts and return top N most frequent phrases
        Filters out phrases that are substrings or semantic duplicates of longer phrases
        
        Args:
            texts: List of English texts to analyze
            top_n: Number of top phrases to return
            min_count: Absolute minimum number of times a phrase must appear (default: 3)
            game_name: Name of the game to filter out self-referential tags
            min_count_ratio: Ratio of max frequency to use as minimum threshold (default: 0.1 = 10%)
            
        Returns:
            List of dicts with 'word' (phrase) and 'count' keys
        """
        all_phrases = []
        
        for text in texts:
            phrases = self.extract_phrases(text)
            all_phrases.extend(phrases)
        
        # Count frequencies
        phrase_counts = Counter(all_phrases)
        
        if not phrase_counts:
            return []
            
        # Adaptive Thresholding Logic
        # Calculate dynamic min_count based on the most frequent phrase
        max_freq = phrase_counts.most_common(1)[0][1]
        dynamic_min = int(max_freq * min_count_ratio)
        
        # Use the higher of the two: absolute min_count OR 10% of max
        # This prevents noisy low-count tags in popular games, while keeping tags in small games
        effective_min_count = max(min_count, dynamic_min)
        
        print(f"[Analyzer] Max freq: {max_freq}, Ratio: {min_count_ratio:.0%}, Dynamic min: {dynamic_min}, Effective min: {effective_min_count}")
        
        # Filter out meta tags and generic phrases (manual list)
        phrase_counts = {
            phrase: count for phrase, count in phrase_counts.items() 
            if phrase.lower() not in self.meta_tags and phrase.lower() not in self.generic_phrases
        }

        # Filter out game name if provided
        if game_name:
            game_name_lower = game_name.lower()
            # Simple token set for more robust checking
            game_tokens = set(word_tokenize(game_name_lower))
            
            phrase_counts = {
                phrase: count for phrase, count in phrase_counts.items()
                # Exclude if phrase is basically the game name (e.g. "black myth" in "Black Myth: Wukong")
                if phrase.lower() not in game_name_lower and game_name_lower not in phrase.lower()
            }
            # Also filter individual tokens if they are unique enough? 
            # Ideally we just filter "black myth" and "wukong"
        
        # 2. Hybrid Approach: Use TextBlob to catch new subjective phrases (auto-filter)
        # Filter out phrases that are too "subjective" (opinions/feelings) rather than objective (facts)
        # e.g., "cant wait" (subjective) vs "open world" (objective)
        final_counts = {}
        for phrase, count in phrase_counts.items():
            # Check subjectivity (0.0 = objective, 1.0 = subjective)
            blob = TextBlob(phrase)
            subjectivity = blob.sentiment.subjectivity
            
            # If subjectivity is high (> 0.5), it's likely an opinion or feeling, not a feature
            # Exception: Some features might have adjectives (e.g., "fast travel"), so be careful with threshold
            # "cant wait" -> 0.6 (if handled correctly?)
            # Let's log suspicious high subjectivity phrases for debugging
            if subjectivity > 0.5:
                print(f"[Subjectivity Filter] Removing '{phrase}' (score: {subjectivity})")
                continue
                
            final_counts[phrase] = count
            
        # Filter by effective minimum count using the final dictionary
        filtered_counts = {phrase: count for phrase, count in final_counts.items() if count >= effective_min_count}
        
        # Get top N from filtered results
        top_phrases = Counter(filtered_counts).most_common(top_n * 2)  # Get extra to account for deduplication
        
        # Deduplicate: Remove phrases that are substrings or semantic duplicates
        deduplicated = []
        phrases_text = [phrase for phrase, _ in top_phrases]
        
        for phrase, count in top_phrases:
            # Check if this phrase is a duplicate of any other phrase
            is_duplicate = False
            phrase_words = set(phrase.split())
            phrase_normalized = set(self._normalize_word(w) for w in phrase_words)
            
            for other_phrase in phrases_text:
                if other_phrase == phrase:
                    continue
                
                # Get count from original phrase_counts (not filtered_counts)
                other_count = phrase_counts.get(other_phrase, 0)
                
                # Check 1: Substring match
                if phrase in other_phrase and other_count >= count:
                    is_duplicate = True
                    break
                
                # Check 2: Word overlap (semantic similarity)
                # Normalize words to handle singular/plural (e.g., "base building" vs "building bases")
                other_words = set(other_phrase.split())
                other_normalized = set(self._normalize_word(w) for w in other_words)
                
                # Calculate overlap ratio using normalized words
                common_words = phrase_normalized & other_normalized
                overlap_ratio = len(common_words) / max(len(phrase_normalized), len(other_normalized))
                
                # Debug logging
                if overlap_ratio >= 0.66:
                    print(f"[Dedup Debug] Comparing '{phrase}' vs '{other_phrase}':")
                    print(f"  Normalized: {phrase_normalized} vs {other_normalized}")
                    print(f"  Overlap: {overlap_ratio:.2%}, Count: {count} vs {other_count}")
                
                # If phrases share >= 66% of words and other has higher count, consider duplicate
                if overlap_ratio >= 0.66 and other_count > count:
                    print(f"[Dedup] Removing '{phrase}' (duplicate of '{other_phrase}')")
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append({'word': phrase, 'count': count})
        
        # Return only top N after deduplication
        return deduplicated[:top_n]
    
    def analyze_reviews_by_sentiment(
        self,
        positive_reviews: List[str],
        negative_reviews: List[str],
        top_n: int = 10,
        min_count: int = 3,
        game_name: str = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Analyze reviews separated by sentiment
        Uses adaptive min_count based on number of reviews
        
        Args:
            positive_reviews: List of positive review texts
            negative_reviews: List of negative review texts
            top_n: Number of top phrases to return for each sentiment
            min_count: Base minimum count for inclusion (default: 3)
            game_name: Name of the game to filter out self-references
            
        Returns:
            Tuple of (positive_tags, negative_tags)
        """
        print(f"[EnglishAnalyzer] Analyzing {len(positive_reviews)} positive and {len(negative_reviews)} negative reviews")
        
        # Adaptive min_count logic: use provided min_count as a baseline
        # If very few reviews, maybe lower it? But user asked for 5 (strict).
        # We will respect the user's min_count primarily.
        
        positive_tags = self.analyze_texts(positive_reviews, top_n, min_count=min_count, game_name=game_name)
        
        # For negative tags, the volume is often much lower (especially for good games).
        # A strict min_count=5 might wipe out all negative tags.
        # We should relax it for negative tags: use roughly half of the strict limit, but at least 2.
        negative_min_count = max(2, int(min_count / 2))
        
        # If we have very few negative reviews (< 20), prevent the 10% adaptive ratio from being too harsh 
        # by passing a lower ratio (e.g. 0.05 or just relying on min_count)
        # But analyze_texts handles max(min, dynamic), so just lowering min_count is enough if dynamic is low.
        
        negative_tags = self.analyze_texts(negative_reviews, top_n, min_count=negative_min_count, game_name=game_name)
        
        print(f"[EnglishAnalyzer] Extracted {len(positive_tags)} positive and {len(negative_tags)} negative tags")
        print(f"[EnglishAnalyzer] Used min_count: positive={min_count}, negative={negative_min_count}")
        
        return positive_tags, negative_tags
