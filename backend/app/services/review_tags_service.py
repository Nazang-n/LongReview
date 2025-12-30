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


class ReviewTagsService:
    """Service for managing game review tags"""
    
    def __init__(self, db: Session):
        self.db = db
        self.thai_analyzer = ThaiTextAnalyzer()
        self.english_analyzer = EnglishTextAnalyzer()
    
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
    
    def generate_tags_for_game(self, game_id: int, top_n: int = 7, language: str = "english", max_reviews: int = 500) -> Dict:
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
