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
from .english_text_analyzer import EnglishTextAnalyzer
from .thai_text_analyzer import ThaiTextAnalyzer
# from .local_llm_service import LocalLLMService # DEPRECATED
from .groq_service import GroqService # NEW FAST AI


class ReviewTagsService:
    """Service for managing game review tags"""
    
    def __init__(self, db: Session):
        self.db = db
        self.thai_analyzer = ThaiTextAnalyzer()
        self.english_analyzer = EnglishTextAnalyzer()
        # self.polisher = LocalLLMService()
        self.polisher = GroqService() # Switch to Groq
        with open("debug_backend.log", "a", encoding="utf-8") as f:
            f.write("[Info] ReviewTagsService initialized with Groq AI.\n")
    
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
        ).all()
        
        negative_tags = self.db.query(GameReviewTag).filter(
            GameReviewTag.game_id == game_id,
            GameReviewTag.tag_type == 'negative'
        ).all()
        
        # Format response (without counts)
        result = {
            'success': True,
            'game_id': game_id,
            'positive_tags': [
                {'tag': tag.tag_word, 'count': 0}
                for tag in positive_tags
            ],
            'negative_tags': [
                {'tag': tag.tag_word, 'count': 0}
                for tag in negative_tags
            ],
            'total_tags': len(positive_tags) + len(negative_tags),
            'last_updated': positive_tags[0].updated_at if positive_tags else None
        }
        
        return result
    
    def generate_tags_for_game(self, game_id: int, top_n: int = 7, language: str = "english", max_reviews: int = 1500) -> Dict:
        """
        Generate tags for a game by analyzing its reviews
        """
        with open("debug_backend.log", "a", encoding="utf-8") as f:
            f.write(f"[Info] generate_tags_for_game called for game {game_id}, lang={language}\n")
        """
        Generate review tags for a game by analyzing ALL reviews from database
        
        Args:
            game_id: Game ID
            top_n: Number of top tags to generate for each sentiment
            language: Review language filter ('english', 'thai', 'all')
            max_reviews: Maximum number of reviews to analyze (default: 1500)
            
        Returns:
            Dict with generated tags and metadata
        """
        from sqlalchemy import text
        
        try:
            # 1. Fetch Game Details (Short Transaction)
            # Get game's name AND steam_app_id from database
            result = self.db.execute(
                text("SELECT name, steam_app_id FROM game WHERE id = :game_id"),
                {"game_id": game_id}
            )
            game_row = result.fetchone()
            
            # Commit/close this read transaction immediately to free the connection?
            # Or just rely on the fact that SELECT doesn't block readers in WAL mode?
            # But SQLite default journal mode blocks writers if readers are active and vice versa?
            # Better to be safe: We have the data, we don't need the DB for the next 30s.
            # self.db.commit() # End current transaction if any
            
            if not game_row:
                return {
                    'success': False,
                    'error': f'Game {game_id} not found',
                    'game_id': game_id
                }
            
            game_name = game_row[0]
            steam_app_id = game_row[1]
            
            if not steam_app_id:
                return {
                    'success': False,
                    'error': f'Game {game_id} has no Steam App ID',
                    'game_id': game_id
                }

            print(f"[ReviewTags] Processing game: {game_name} (ID: {game_id}, SteamID: {steam_app_id})")
            
            # --- CRITICAL: RELEASE DB LOCK HERE ---
            # We are about to do a long network call (30s+). 
            # If we keep the session active, we might hold a lock or transaction.
            # Especially with SQLite or certain isolation levels.
            # We can't easily "close" the session provided by dependency, but we can avoid using it.
            # The session is passed in __init__.
            
            # 2. Fetch English reviews DIRECTLY from Steam API for analysis (LONG OP)
            # This happens OUTSIDE of any DB lock/transaction hopefully.
            from ..steam_api import SteamAPIClient
            with open("debug_backend.log", "a", encoding="utf-8") as f:
                f.write(f"[Info] Fetching English reviews from Steam API (max={max_reviews})...\n")
            
            steam_reviews = SteamAPIClient.get_all_reviews(
                app_id=int(steam_app_id),
                language="english",
                max_reviews=max_reviews # Use parameterized limit
            )
            
            with open("debug_backend.log", "a", encoding="utf-8") as f:
                f.write(f"[Info] Got {len(steam_reviews) if steam_reviews else 0} reviews from Steam API\n")
            
            if not steam_reviews:
                 return {
                    'success': False,
                    'error': f'No English reviews found on Steam for analysis.',
                    'game_id': game_id
                }

            # Format reviews for analyzer
            db_reviews = []
            for r in steam_reviews:
                content = r.get('review', '')
                voted = r.get('voted_up', True)
                votes_up = r.get('votes_up', 0)
                if content:
                    db_reviews.append({
                        'content': content,
                        'voted_up': voted,
                        'votes_up': votes_up
                    })
            
            # Separate reviews by sentiment
            positive_reviews_data = [r for r in db_reviews if r['voted_up'] == True]
            negative_reviews_data = [r for r in db_reviews if r['voted_up'] == False]
            
            # ATTEMPT 1: Classic (Full Input)
            print(f"[ReviewTags] Attempt 1: Classic Mode (Full {len(positive_reviews_data)}/{len(negative_reviews_data)})")
            
            positive_reviews = [r['content'] for r in positive_reviews_data]
            negative_reviews = [r['content'] for r in negative_reviews_data]

            if language == "english":
                # --- AI APPROACH ---
                with open("debug_backend.log", "a", encoding="utf-8") as f:
                    f.write(f"[Info] Attempt 1: Using Groq AI with FULL context...\n")

                ai_summary = self.polisher.summarize_reviews(positive_reviews, negative_reviews)
                
                # Check for Rate Limit Fallback
                if ai_summary is None:
                    print(f"[ReviewTags] Attempt 1 Failed (Rate Limit). Switching to Hybrid Fallback...")
                    with open("debug_backend.log", "a", encoding="utf-8") as f:
                        f.write(f"[Info] Rate Limit Hit! Engaging Hybrid Strategy (Top 30 + Truncate)...\n")
                    
                    # ATTEMPT 2: Hybrid Fallback (Smart Filter)
                    # 1. Filter Short
                    positive_reviews_data = [r for r in positive_reviews_data if len(r['content']) >= 30]
                    negative_reviews_data = [r for r in negative_reviews_data if len(r['content']) >= 30]
                    
                    # 2. Sort by Helpfulness
                    positive_reviews_data.sort(key=lambda x: x['votes_up'], reverse=True)
                    negative_reviews_data.sort(key=lambda x: x['votes_up'], reverse=True)
                    
                    # 3. Slice Top 30
                    top_positive = positive_reviews_data[:30]
                    top_negative = negative_reviews_data[:30]
                    
                    # 4. Extract & Truncate to 300 chars
                    positive_reviews = [r['content'][:300] for r in top_positive]
                    negative_reviews = [r['content'][:300] for r in top_negative]
                    
                    with open("debug_backend.log", "a", encoding="utf-8") as f:
                         f.write(f"[Info] Fallback Stats: Sent {len(positive_reviews)} Pos / {len(negative_reviews)} Neg\n")

                    # Retry AI
                    ai_summary = self.polisher.summarize_reviews(positive_reviews, negative_reviews)
                    if ai_summary is None:
                         # Still failed? Return empty to avoid crashes
                         ai_summary = {"positive": [], "negative": []}

                
                # Convert AI JSON to Frontend format List[{ 'word': tag, 'count': x }]
                # AI returns ordered list (Most important first). Set count to 0 since they're not real counts.
                
                positive_tags = []
                for tag in ai_summary.get("positive", []):
                    positive_tags.append({'word': tag, 'count': 0})
                    
                negative_tags = []
                for tag in ai_summary.get("negative", []):
                    negative_tags.append({'word': tag, 'count': 0})
                    
                with open("debug_backend.log", "a", encoding="utf-8") as f:
                     f.write(f"[Info] AI Summary Complete. Pos: {len(positive_tags)}, Neg: {len(negative_tags)}\n")
                
                # --- OLD APPROACH: Rule-based EnglishTextAnalyzer (COMMENTED OUT) ---
                # base_min_count = 2 if len(positive_reviews) < 200 else 5
                # print(f"[ReviewTags] Using EnglishTextAnalyzer (min_count={base_min_count}, filtering '{game_name}')")
                # positive_tags, negative_tags = self.english_analyzer.analyze_reviews_by_sentiment(
                #     positive_reviews,
                #     negative_reviews,
                #     top_n,
                #     min_count=base_min_count,
                #     game_name=game_name
                # )

            else:
                analyzer = self.thai_analyzer
                print("[ReviewTags] Using ThaiTextAnalyzer")
                positive_tags, negative_tags = analyzer.analyze_reviews_by_sentiment(
                    positive_reviews,
                    negative_reviews,
                    top_n
                )
            
            # --- Deduplication & Game Name Filtering (ONLY for Thai, AI handles English) ---
            if language != "english":
                import re
                def normalize_text(text):
                    return re.sub(r'[^a-z0-9]', '', text.lower())
                
                norm_game_name = normalize_text(game_name)
                
                def is_title_tag(tag_word):
                    norm_tag = normalize_text(tag_word)
                    if norm_tag == norm_game_name:
                        return True
                    if len(norm_tag) > 5 and (norm_tag in norm_game_name or norm_game_name in norm_tag):
                         return True
                    return False

                positive_tags = [t for t in positive_tags if not is_title_tag(t['word'])]
                negative_tags = [t for t in negative_tags if not is_title_tag(t['word'])]
                
                # Resolve Conflicting Tags (Dominance Rule)
                pos_dict = {tag['word']: tag['count'] for tag in positive_tags}
                neg_dict = {tag['word']: tag['count'] for tag in negative_tags}
                
                final_pos_tags = []
                final_neg_tags = []
                
                for tag in positive_tags:
                    word = tag['word']
                    p_count = tag['count']
                    n_count = neg_dict.get(word, 0)
                    if n_count > p_count:
                        continue 
                    elif n_count == p_count and n_count > 0:
                         pass 
                    final_pos_tags.append(tag)
                    
                for tag in negative_tags:
                    word = tag['word']
                    n_count = tag['count']
                    p_count = pos_dict.get(word, 0)
                    if p_count >= n_count:
                        continue
                    final_neg_tags.append(tag)
                
                positive_tags = final_pos_tags
                negative_tags = final_neg_tags
                
                # --- AI Polishing Step for Thai ---
                try:
                    all_tag_words = [t['word'] for t in positive_tags] + [t['word'] for t in negative_tags]
                    if all_tag_words:
                        print(f"[ReviewTags] Polishing {len(all_tag_words)} tags with AI...")
                        polished_map = self.polisher.polish_and_translate_tags(all_tag_words)
                        
                        for tag in positive_tags:
                            tag['word'] = polished_map.get(tag['word'], tag['word'])
                        for tag in negative_tags:
                            tag['word'] = polished_map.get(tag['word'], tag['word'])
                        print("[ReviewTags] AI Polishing complete.")
                        
                except Exception as e:
                    print(f"[ReviewTags] AI Polishing failed (skipping): {e}")
                        


            # 4. Save to Database (Short Write Transaction)
            # Re-verify game existence or just write?
            # We wrap this in a commit to ensure atomic write.
            
            # Delete existing tags
            self.db.query(GameReviewTag).filter(
                GameReviewTag.game_id == game_id
            ).delete()
            
            # Save positive tags
            for tag_data in positive_tags:
                tag = GameReviewTag(
                    game_id=game_id,
                    tag_type='positive',
                    tag_word=tag_data['word']
                )
                self.db.add(tag)
            
            # Save negative tags
            for tag_data in negative_tags:
                tag = GameReviewTag(
                    game_id=game_id,
                    tag_type='negative',
                    tag_word=tag_data['word']
                )
                self.db.add(tag)
            
            self.db.commit()
            
            print(f"[ReviewTags] Saved {len(positive_tags)} positive and {len(negative_tags)} negative tags")
            
            return {
                'success': True,
                'game_id': game_id,
                'positive_tags': positive_tags,
                'negative_tags': negative_tags,
                'total_reviews_analyzed': len(db_reviews),
                'positive_reviews': len(positive_reviews),
                'negative_reviews': len(negative_reviews),
                'language': language,
                'source': 'database',  # Changed from 'steam_api' to 'database'
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
    
    def refresh_tags_if_needed(self, game_id: int, max_age_days: int = 7, max_reviews: int = 1500) -> Dict:
        """
        Refresh tags if they are older than max_age_days or don't exist
        
        Args:
            game_id: Game ID
            max_age_days: Maximum age of tags in days before refresh
            max_reviews: limit reviews for generation if needed
            
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
        return self.generate_tags_for_game(game_id, max_reviews=max_reviews)
