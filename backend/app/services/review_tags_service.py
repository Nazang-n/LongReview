"""
Review Tags Service
Manages game review tags - generation, storage, and retrieval
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models import GameReviewTag, Review
from .thai_text_analyzer import ThaiTextAnalyzer
from .english_text_analyzer import EnglishTextAnalyzer
from .tag_polisher_service import TagPolisherService


class ReviewTagsService:
    """Service for managing game review tags"""
    
    def __init__(self, db: Session):
        self.db = db
        self.thai_analyzer = ThaiTextAnalyzer()
        self.english_analyzer = EnglishTextAnalyzer()
        self.polisher = TagPolisherService()
    
    def get_tags_for_game(self, game_id: int) -> Dict:
        """
        Get review tags for a game from database
        
        Args:
            game_id: Game ID
            
        Returns:
            Dict with positive_tags, negative_tags, and metadata
        """
        # Query tags from database
        positive_tags = self.db.query(GameReviewTag).filter(
            GameReviewTag.game_id == game_id,
            GameReviewTag.tag_type == 'positive'
        ).order_by(GameReviewTag.tag_count.desc()).all()
        
        negative_tags = self.db.query(GameReviewTag).filter(
            GameReviewTag.game_id == game_id,
            GameReviewTag.tag_type == 'negative'
        ).order_by(GameReviewTag.tag_count.desc()).all()
        
        # Format response
        result = {
            'success': True,
            'game_id': game_id,
            'positive_tags': [
                {'tag': tag.tag_word, 'count': tag.tag_count}
                for tag in positive_tags
            ],
            'negative_tags': [
                {'tag': tag.tag_word, 'count': tag.tag_count}
                for tag in negative_tags
            ],
            'total_tags': len(positive_tags) + len(negative_tags),
            'last_updated': positive_tags[0].updated_at if positive_tags else None
        }
        
        return result
    
    def generate_tags_for_game(self, game_id: int, top_n: int = 7, language: str = "english", max_reviews: int = 1500) -> Dict:
        """
        Generate review tags for a game by fetching and analyzing Steam reviews
        
        Args:
            game_id: Game ID
            top_n: Number of top tags to generate for each sentiment
            language: Review language ('english', 'thai', 'all')
            max_reviews: Maximum number of reviews to fetch from Steam
            
        Returns:
            Dict with generated tags and metadata
        """
        from ..steam_api import SteamAPIClient
        from sqlalchemy import text
        
        try:
            # Get game's steam_app_id and name from database
            result = self.db.execute(
                text("SELECT steam_app_id, name FROM game WHERE id = :game_id"),
                {"game_id": game_id}
            )
            game_row = result.fetchone()
            
            if not game_row or not game_row[0]:
                return {
                    'success': False,
                    'error': f'Game {game_id} not found or has no steam_app_id',
                    'game_id': game_id
                }
            
            steam_app_id = int(game_row[0])
            game_name = game_row[1]
            print(f"[ReviewTags] Processing game: {game_name} (AppID: {steam_app_id})")
            
            # Fetch reviews directly from Steam API
            print(f"[ReviewTags] Fetching {max_reviews} {language} reviews for app {steam_app_id}...")
            steam_reviews = SteamAPIClient.get_all_reviews(
                app_id=steam_app_id,
                language=language,
                max_reviews=max_reviews
            )
            
            if not steam_reviews:
                return {
                    'success': False,
                    'error': f'No {language} reviews found on Steam',
                    'game_id': game_id
                }
            
            print(f"[ReviewTags] Got {len(steam_reviews)} reviews from Steam")
            
            # Separate reviews by sentiment (voted_up)
            positive_reviews = [r.get('review', '') for r in steam_reviews if r.get('voted_up') == True]
            negative_reviews = [r.get('review', '') for r in steam_reviews if r.get('voted_up') == False]
            
            print(f"[ReviewTags] Positive: {len(positive_reviews)}, Negative: {len(negative_reviews)}")
            
            # Select analyzer based on language
            if language == "english":
                # Use updated min_count (5) and game_name filter for English
                print(f"[ReviewTags] Using EnglishTextAnalyzer (min_count=5, filtering '{game_name}')")
                positive_tags, negative_tags = self.english_analyzer.analyze_reviews_by_sentiment(
                    positive_reviews,
                    negative_reviews,
                    top_n,
                    min_count=5,  # Increased threshold as requested
                    game_name=game_name
                )
            else:
                analyzer = self.thai_analyzer
                print("[ReviewTags] Using ThaiTextAnalyzer")
                # Thai analyzer might not support these new arguments yet?
                # Assuming ThaiAnalyzer matches old signature or handles *args, **kwargs.
                # Actually, ThaiTextAnalyzer inheritance or strict typing?
                # Let's check ThaiTextAnalyzer signature if needed. But for now, just calling the old way for ELSE block if needed.
                # Wait, ThaiTextAnalyzer likely has the old signature.
                positive_tags, negative_tags = analyzer.analyze_reviews_by_sentiment(
                    positive_reviews,
                    negative_reviews,
                    top_n
                )
            
            # --- GOLDEN RULE: Deduplication & Game Name Filtering ---
            # 1. Clean up Game Name Tags (e.g. remove "Black Myth Wukong" tag from "Black Myth: Wukong")
            # Create a normalized version of game name for comparison (remove spaces/conduct punctuation)
            import re
            def normalize_text(text):
                return re.sub(r'[^a-z0-9]', '', text.lower())
            
            norm_game_name = normalize_text(game_name)
            
            def is_title_tag(tag_word):
                norm_tag = normalize_text(tag_word)
                # Check if tag is essentially the game name (or very close)
                # Equal, or contained if it's long enough to be significant
                if norm_tag == norm_game_name:
                    return True
                if len(norm_tag) > 5 and (norm_tag in norm_game_name or norm_game_name in norm_tag):
                     return True
                return False

            positive_tags = [t for t in positive_tags if not is_title_tag(t['word'])]
            negative_tags = [t for t in negative_tags if not is_title_tag(t['word'])]
            
            # 2. Resolve Conflicting Tags (Dominance Rule)
            # If a tag exists in both, keep ONLY the one with higher count.
            # If counts are equal, default to Positive (or maybe remove both? taking Positive for now).
            
            # Re-build dictionaries after title filtering
            pos_dict = {tag['word']: tag['count'] for tag in positive_tags}
            neg_dict = {tag['word']: tag['count'] for tag in negative_tags}
            
            final_pos_tags = []
            final_neg_tags = []
            
            # Process Positive: Keep if Count > Negative Count
            for tag in positive_tags:
                word = tag['word']
                p_count = tag['count']
                n_count = neg_dict.get(word, 0)
                
                if n_count > p_count:
                    print(f"[ReviewTags] Dominance: '{word}' is more NEGATIVE ({n_count} > {p_count}). Removing from Positive.")
                    continue # Skip (it belongs to Negative)
                elif n_count == p_count and n_count > 0:
                     # Tie-breaker: Maybe keep positive? Or remove?
                     # User said "If which side has more...". If equal, maybe ambiguous.
                     # Let's keep in Positive as default benefit of doubt.
                     pass 
                
                final_pos_tags.append(tag)
                
            # Process Negative: Keep if Count > Positive Count
            # Note: We use > so that if equal, it fails here (since we kept it in Positive above)
            for tag in negative_tags:
                word = tag['word']
                n_count = tag['count']
                p_count = pos_dict.get(word, 0)
                
                if p_count >= n_count: # If Positive is deeper or equal, we removed it from Negative
                    if p_count > 0:
                        print(f"[ReviewTags] Dominance: '{word}' is more POSITIVE (or equal) ({p_count} >= {n_count}). Removing from Negative.")
                    continue
                
                final_neg_tags.append(tag)
            
            positive_tags = final_pos_tags
            negative_tags = final_neg_tags
            # ----------------------------------------------
            
            # --- AI Polishing Step (DISABLED) ---
            # if language == "english":
            #     try:
            #         all_tag_words = [t['word'] for t in positive_tags] + [t['word'] for t in negative_tags]
            #         if all_tag_words:
            #             print(f"[ReviewTags] Polishing {len(all_tag_words)} tags with AI...")
            #             polished_map = self.polisher.polish_tags(all_tag_words)
            #             
            #             # Apply polished words
            #             for tag in positive_tags:
            #                 tag['word'] = polished_map.get(tag['word'], tag['word'])
            #                 
            #             for tag in negative_tags:
            #                 tag['word'] = polished_map.get(tag['word'], tag['word'])
            #             print("[ReviewTags] AI Polishing complete.")
            #     except Exception as e:
            #         print(f"[ReviewTags] AI Polishing failed (skipping): {e}")
            # -------------------------------

            # Delete existing tags for this game
            self.db.query(GameReviewTag).filter(
                GameReviewTag.game_id == game_id
            ).delete()
            
            # Save positive tags
            for tag_data in positive_tags:
                tag = GameReviewTag(
                    game_id=game_id,
                    tag_type='positive',
                    tag_word=tag_data['word'],
                    tag_count=tag_data['count']
                )
                self.db.add(tag)
            
            # Save negative tags
            for tag_data in negative_tags:
                tag = GameReviewTag(
                    game_id=game_id,
                    tag_type='negative',
                    tag_word=tag_data['word'],
                    tag_count=tag_data['count']
                )
                self.db.add(tag)
            
            self.db.commit()
            
            print(f"[ReviewTags] Saved {len(positive_tags)} positive and {len(negative_tags)} negative tags")
            
            return {
                'success': True,
                'game_id': game_id,
                'positive_tags': positive_tags,
                'negative_tags': negative_tags,
                'total_reviews_analyzed': len(steam_reviews),
                'positive_reviews': len(positive_reviews),
                'negative_reviews': len(negative_reviews),
                'language': language,
                'source': 'steam_api',
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"[ReviewTags] Error: {e}")
            return {
                'success': False,
                'error': str(e),
                'game_id': game_id
            }
    
    def refresh_tags_if_needed(self, game_id: int, max_age_days: int = 7) -> Dict:
        """
        Refresh tags if they are older than max_age_days or don't exist
        
        Args:
            game_id: Game ID
            max_age_days: Maximum age of tags in days before refresh
            
        Returns:
            Dict with tags (either from cache or newly generated)
        """
        # Check if tags exist and are recent
        existing_tags = self.db.query(GameReviewTag).filter(
            GameReviewTag.game_id == game_id
        ).first()
        
        if existing_tags:
            age = datetime.now() - existing_tags.updated_at.replace(tzinfo=None)
            if age < timedelta(days=max_age_days):
                # Tags are fresh, return from database
                return self.get_tags_for_game(game_id)
        
        # Tags don't exist or are old, generate new ones
        return self.generate_tags_for_game(game_id)
