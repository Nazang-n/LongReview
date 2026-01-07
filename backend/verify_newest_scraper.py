from app.steam_api import SteamAPIClient
import json

def test_scraper():
    print("Testing Steam Store Scraper...")
    games = SteamAPIClient.get_newest_games_from_steam_store(limit=10)
    
    if games:
        print(f"Successfully fetched {len(games)} games.")
        for game in games:
            print(f"- [{game['app_id']}] {game['name']} ({game['release_date_str']})")
    else:
        print("Failed to fetch games.")

if __name__ == "__main__":
    test_scraper()
