import requests
import json

def check_steamspy_structure():
    url = "https://steamspy.com/api.php?request=all&page=0"
    print(f"Fetching {url}...")
    try:
        # Fetch just a small chunk if possible, but the API returns a huge JSON.
        # We'll just read the response and break early or parse it.
        # Actually requests.get will download the whole body before .json()
        # But for 'all', it's large (10MB+).
        # Let's try 'request=top100forever' which is smaller but likely has same schema.
        url_top = "https://steamspy.com/api.php?request=top100forever"
        response = requests.get(url_top, timeout=30)
        data = response.json()
        
        # Get first item
        first_item = list(data.values())[0] if data else None
        
        print("Keys in SteamSpy response item:")
        if first_item:
            for k, v in first_item.items():
                print(f"  {k}: {v} (Type: {type(v)})")
        else:
            print("No data found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_steamspy_structure()
