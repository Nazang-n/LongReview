from app.steam_api import SteamAPIClient
from app.services.english_text_analyzer import EnglishTextAnalyzer

def debug_analysis():
    app_id = 1903340
    print(f"Fetching reviews for {app_id}...")
    reviews = SteamAPIClient.get_all_reviews(app_id, language='english', max_reviews=100)
    
    if not reviews:
        print("No reviews found.")
        return

    # Extract text from reviews
    texts = [r.get('review', '') for r in reviews if r.get('review')]
    print(f"Analyzing {len(texts)} reviews...")
    
    analyzer = EnglishTextAnalyzer()
    
    # Test with min_count=2
    print("\n--- Test with min_count=2 ---")
    tags = analyzer.analyze_texts(texts, top_n=20, min_count=2, game_name="Clair Obscur: Expedition 33")
    for t in tags:
        print(f"- {t['word']} ({t['count']})")
        
    # Test with min_count=1
    print("\n--- Test with min_count=1 (Noise check) ---")
    tags_1 = analyzer.analyze_texts(texts, top_n=20, min_count=1, game_name="Clair Obscur: Expedition 33")
    for t in tags_1:
        print(f"- {t['word']} ({t['count']})")

if __name__ == "__main__":
    debug_analysis()
