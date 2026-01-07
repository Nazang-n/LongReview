import requests
import json

def check_steam_reviews(app_id):
    url = f"https://store.steampowered.com/appreviews/{app_id}"
    
    scenarios = [
        {"name": "Default (no extra params)", "params": {"json": 1, "language": "all", "num_per_page": 0}},
        {"name": "Purchase: steam_purchase", "params": {"json": 1, "language": "all", "num_per_page": 0, "purchase_type": "steam_purchase"}},
        {"name": "Purchase: all", "params": {"json": 1, "language": "all", "num_per_page": 0, "purchase_type": "all"}},
        {"name": "Language: thai", "params": {"json": 1, "language": "thai", "num_per_page": 0, "purchase_type": "all"}},
    ]

    print(f"Checking Review Counts for App ID: {app_id}\n")
    
    for scenario in scenarios:
        try:
            response = requests.get(url, params=scenario["params"], timeout=10)
            data = response.json()
            if data.get('success') == 1:
                summary = data.get('query_summary', {})
                total = summary.get('total_reviews', 0)
                print(f"Scenario: {scenario['name']}")
                print(f"  Total Reviews: {total}")
                print("-" * 30)
            else:
                print(f"Scenario: {scenario['name']} - Failed")
        except Exception as e:
            print(f"Scenario: {scenario['name']} - Error: {e}")

if __name__ == "__main__":
    # Content Warning App ID is 2881650
    check_steam_reviews(2881650)
