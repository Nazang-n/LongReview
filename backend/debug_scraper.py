from app.steam_api import SteamAPIClient
import requests
import re

def inspect_html():
    url = "https://store.steampowered.com/search/?sort_by=Released_DESC&category1=998&os=win"
    print(f"Fetching {url }...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    html = response.text
    
    rows = html.split('class="search_result_row')
    if len(rows) > 1:
        print("--- First Row HTML Snippet ---")
        print(rows[1][:1000]) # Print first 1000 chars of the first row
        print("------------------------------")
        
        # Test regex locally
        row_html = rows[1]
        date_match = re.search(r'<div class="col search_released responsive_secondrow">(.*?)</div>', row_html, re.DOTALL)
        print(f"Regex match result: {date_match.group(1) if date_match else 'NO MATCH'}")

if __name__ == "__main__":
    inspect_html()
