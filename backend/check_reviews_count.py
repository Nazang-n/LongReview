from app.steam_api import SteamAPIClient

def check_reviews():
    app_id = 1903340
    print(f"Fetching reviews for {app_id}...")
    
    # Try fetching English reviews
    reviews_en = SteamAPIClient.get_all_reviews(app_id, language='english', max_reviews=100)
    print(f"English Reviews Count: {len(reviews_en)}")
    if reviews_en:
        print(f"Sample: {reviews_en[0].get('review')[:50]}...")
        
    # Try fetching Thai reviews
    reviews_th = SteamAPIClient.get_all_reviews(app_id, language='thai', max_reviews=100)
    print(f"Thai Reviews Count: {len(reviews_th)}")

if __name__ == "__main__":
    check_reviews()
