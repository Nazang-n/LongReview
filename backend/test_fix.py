import sys
import os

# Add the parent directory to sys.path so we can import the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.steam_api import SteamAPIClient

def test_steam_api_client():
    app_id = 2881650 # Content Warning
    print(f"Testing SteamAPIClient for App ID: {app_id}")
    
    # Test get_app_reviews (default)
    print("\n--- Test 1: get_app_reviews (default) ---")
    data = SteamAPIClient.get_app_reviews(app_id, language="all", num_per_page=0)
    if data and data.get('success') == 1:
        summary = data.get('query_summary', {})
        total = summary.get('total_reviews', 0)
        print(f"Total Reviews: {total}")
        if total > 100000:
            print("SUCCESS: Count matches 'All Reviews' (Store Page)")
        else:
            print("FAILURE: Count matches 'Steam Purchasers' only (likely still mismatch)")
    else:
        print("API Call Failed")

if __name__ == "__main__":
    test_steam_api_client()
