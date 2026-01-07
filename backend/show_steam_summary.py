import sys
import os
import json

# Add the parent directory to sys.path so we can import the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.steam_api import SteamAPIClient

def show_summary():
    app_id = 1903340 # Clair Obscur: Expedition 33
    print(f"Fetching Steam API Summary for Clair Obscur: Expedition 33 (App ID: {app_id})...\n")
    
    # ensure purchase_type='all' is used (default now)
    data = SteamAPIClient.get_app_reviews(app_id, language="all", num_per_page=0)
    
    if data and data.get('success') == 1:
        summary = data.get('query_summary', {})
        print("--- Steam API Response (query_summary) ---")
        print(json.dumps(summary, indent=4))
        print("------------------------------------------")
        
        pos = summary.get('total_positive', 0)
        neg = summary.get('total_negative', 0)
        total = summary.get('total_reviews', 0)
        
        print(f"\nVerification:")
        print(f"Positive: {pos:,}")
        print(f"Negative: {neg:,}")
        print(f"Total:    {total:,} (Matches {pos+neg:,})")
    else:
        print("Failed to fetch data")

if __name__ == "__main__":
    show_summary()
