"""
Test script to check if EnglishTextAnalyzer works
"""
import sys
sys.path.insert(0, 'D:/LongReviewV2/LongReview/backend')

try:
    from app.services.english_text_analyzer import EnglishTextAnalyzer
    print("✅ Import successful!")
    
    analyzer = EnglishTextAnalyzer()
    print("✅ Analyzer created!")
    
    # Test with sample text
    test_reviews = [
        "This is a great game with amazing story and fun gameplay",
        "The online mode is really good"
    ]
    
    tags = analyzer.analyze_texts(test_reviews, top_n=5)
    print("✅ Analysis successful!")
    print(f"Tags: {tags}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
