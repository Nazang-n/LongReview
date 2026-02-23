import requests
from typing import Optional, Dict, Any, List
import time
import re


class SteamAPIClient:
    """Client for fetching data from Steam API"""
    
    BASE_URL = "https://store.steampowered.com"
    STEAMSPY_BASE_URL = "https://steamspy.com/api.php"
    
    @staticmethod
    def get_app_reviews(
        app_id: int,
        language: str = "thai",
        filter_type: str = "all",
        purchase_type: str = "all",
        cursor: str = "*",
        num_per_page: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch reviews for a specific Steam app
        
        Args:
            app_id: Steam application ID
            language: Language filter (e.g., 'thai', 'english')
            filter_type: Filter type ('all', 'recent', 'updated')
            purchase_type: Purchase type ('all', 'steam_purchase', 'non_steam_purchase')
            cursor: Pagination cursor
            num_per_page: Number of reviews per page
            
        Returns:
            Dictionary containing reviews data or None if failed
        """
        url = f"{SteamAPIClient.BASE_URL}/appreviews/{app_id}"
        
        params = {
            "json": "1",
            "filter": filter_type,
            "language": language,
            "purchase_type": purchase_type,
            "cursor": cursor,
            "num_per_page": num_per_page
        }
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Increased timeout to 30s as Steam API can be slow/rate-limited
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    print(f"Rate limit hit for app {app_id}. Waiting {retry_delay*5}s...")
                    time.sleep(retry_delay * 5)
                    raise requests.exceptions.RequestException("Rate limit")
                    
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching Steam reviews (Attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    return None
    
    @staticmethod
    def get_all_reviews(
        app_id: int,
        language: str = "thai",
        purchase_type: str = "all",
        max_reviews: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all reviews for a Steam app (with pagination)
        
        Args:
            app_id: Steam application ID
            language: Language filter
            purchase_type: Purchase type filter
            max_reviews: Maximum number of reviews to fetch (None = all)
            
        Returns:
            List of review dictionaries
        """
        all_reviews = []
        cursor = "*"
        previous_cursor = None
        
        while True:
            previous_count = len(all_reviews)
            
            data = SteamAPIClient.get_app_reviews(
                app_id=app_id,
                language=language,
                purchase_type=purchase_type,
                cursor=cursor
            )
            
            print(f"[DEBUG] Steam API response: success={data.get('success') if data else None}, reviews={len(data.get('reviews', [])) if data else 0}")
            
            if not data or data.get("success") != 1:
                print(f"[WARNING] Steam API failed or returned no data")
                break
            
            reviews = data.get("reviews", [])
            if not reviews:
                print(f"[DEBUG] No reviews in response")
                break
            
            all_reviews.extend(reviews)
            
            # Check if we actually got new reviews
            if len(all_reviews) == previous_count:
                # No new reviews added, break to prevent infinite loop
                print(f"[DEBUG] No new reviews fetched, stopping pagination")
                break
            
            # Check if we've reached max_reviews
            if max_reviews and len(all_reviews) >= max_reviews:
                all_reviews = all_reviews[:max_reviews]
                break
            
            # Get next cursor for pagination
            new_cursor = data.get("cursor")
            if not new_cursor or new_cursor == cursor:
                # No more pages or cursor didn't change (prevent infinite loop)
                print(f"[DEBUG] Pagination complete or cursor unchanged")
                break
            
            cursor = new_cursor
            
            # Be nice to Steam API - add small delay
            time.sleep(0.5)
        
        return all_reviews
    
    @staticmethod
    def get_app_details(app_id: int, language: str = "thai", country_code: str = "th") -> Optional[Dict[str, Any]]:
        """
        Fetch app details from Steam with language support
        
        Args:
            app_id: Steam application ID
            language: Language code (e.g., 'thai', 'english')
            country_code: Country code for pricing (e.g., 'th', 'us')
            
        Returns:
            Dictionary containing app details or None if failed
        """
        url = f"{SteamAPIClient.BASE_URL}/api/appdetails"
        params = {
            "appids": app_id,
            "cc": country_code,  # Country code for pricing
            "l": language  # Language
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if str(app_id) in data and data[str(app_id)]["success"]:
                return data[str(app_id)]["data"]
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Steam app details: {e}")
            return None
    
    @staticmethod
    def get_all_games_from_steamspy(
        page: int = 0,
        limit: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch all games from SteamSpy API
        
        Args:
            page: Page number (for pagination)
            limit: Limit number of games returned (None = all)
            
        Returns:
            Dictionary with app_id as keys and game data as values
        """
        url = SteamAPIClient.STEAMSPY_BASE_URL
        params = {"request": "all", "page": page}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if limit:
                # Convert to list of items, slice, and convert back to dict
                items = list(data.items())[:limit]
                return dict(items)
            
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching SteamSpy data: {e}")
            return None
    
    @staticmethod
    def get_game_details_from_steamspy(app_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed game information from SteamSpy
        
        Args:
            app_id: Steam application ID
            
        Returns:
            Dictionary containing game details from SteamSpy
        """
        url = SteamAPIClient.STEAMSPY_BASE_URL
        params = {"request": "appdetails", "appid": app_id}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching SteamSpy game details: {e}")
            return None
    
    @staticmethod
    def get_top_games_from_steamspy(limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch top games by player count from SteamSpy
        
        Args:
            limit: Number of top games to fetch
            
        Returns:
            List of game dictionaries sorted by player count
        """
        all_games = SteamAPIClient.get_all_games_from_steamspy()
        
        if not all_games:
            return None
        
        # Convert to list and sort by player count
        games_list = []
        for app_id, game_data in all_games.items():
            game_data['app_id'] = app_id
            games_list.append(game_data)
        
        # Sort by owners (player count) in descending order
        sorted_games = sorted(
            games_list,
            key=lambda x: x.get('owners', 0),
            reverse=True
        )
        
        return sorted_games[:limit]
    
    @staticmethod
    def get_newest_games_from_steamspy(limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch newest games by release date from SteamSpy.

        Steam assigns App IDs sequentially, so a higher app_id means the game
        was added to Steam more recently. Sorting by app_id descending gives
        the most recently released games first — no scraping required.

        Args:
            limit: Number of newest games to fetch

        Returns:
            List of game dictionaries sorted by app_id descending (newest first)
        """
        all_games = SteamAPIClient.get_all_games_from_steamspy()

        if not all_games:
            return None

        # Convert to list and embed the numeric app_id for sorting
        games_list = []
        for app_id, game_data in all_games.items():
            try:
                numeric_id = int(app_id)
            except (ValueError, TypeError):
                continue
            game_data['app_id'] = app_id
            game_data['_app_id_int'] = numeric_id
            games_list.append(game_data)

        # Sort by app_id descending — highest ID = most recently added to Steam
        sorted_games = sorted(
            games_list,
            key=lambda x: x.get('_app_id_int', 0),
            reverse=True
        )

        return sorted_games[:limit]

    @staticmethod
    def get_newest_games_from_steam_store(limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch newest games by scraping Steam Store Search
        Url: https://store.steampowered.com/search/?sort_by=Released_DESC&category1=998&os=win
        
        Args:
            limit: Number of games to fetch
            
        Returns:
            List of game dictionaries with 'app_id', 'name', 'release_date_str'
        """
        base_url = "https://store.steampowered.com/search/"
        games_list = []
        page = 1
        
        while len(games_list) < limit:
            params = {
                "sort_by": "Released_DESC",
                "category1": "998", # Games
                "os": "win",
                "page": page
            }
            
            try:
                print(f"Scraping Steam Store Search page {page}...")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(base_url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                html = response.text
                
                # Optimization: Split by 'search_result_row' to avoid catastrophic backtracking
                # Each game is in a <a ... class="search_result_row ..."> container
                
                rows = html.split('class="search_result_row')
                
                # Skip the first chunk (header/nav before first result)
                for row_html in rows[1:]:
                    # Check if this row is actually a game (has appid)
                    # Pattern to extract app_id, Name, and Date from the row chunk
                    # Note: We don't need DOTALL as much if we just match within the chunk, 
                    # but newlines might still exist.
                    
                    app_match = re.search(r'data-ds-appid="(\d+)"', row_html)
                    title_match = re.search(r'<span class="title">(.*?)</span>', row_html, re.DOTALL)
                    # Relaxed regex to handle potential extra classes or whitespace
                    date_match = re.search(r'<div class="[^"]*search_released[^"]*">(.*?)</div>', row_html, re.DOTALL)
                    
                    if app_match and title_match:
                        app_id = int(app_match.group(1))
                        title = title_match.group(1).strip()
                        date_str = date_match.group(1).strip() if date_match else "Unknown"
                        
                        # Filter duplicates
                        if any(g['app_id'] == app_id for g in games_list):
                            continue
                            
                        # Add to list
                        games_list.append({
                            'app_id': app_id,
                            'name': title,
                            'release_date_str': date_str,
                            'developer': '',
                            'publisher': '',
                            'score_rank': '',
                            'owners': '0 .. 20,000'
                        })
                        
                        if len(games_list) >= limit:
                            break
                            
                if not games_list:
                    print(f"No games found on page {page}")
                
                page += 1
                time.sleep(1) # Be clean
                
            except Exception as e:
                print(f"Error scraping Steam Store: {e}")
                break

                
        return games_list[:limit]

    @staticmethod
    def get_all_games_list() -> Optional[List[Dict[str, Any]]]:
        """
        Fetch complete list of apps from Steam
        Url: https://api.steampowered.com/IStoreService/GetAppList/v1/
        """
        # User provided API Key: 925DACE9202850368554F7061C00EDCD
        # NOTE: Using a hardcoded key in code is generally bad practice, 
        # but requested by user for this specific implementation.
        # Should ideally be in env vars.
        
        url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
        params = {
            "key": "925DACE9202850368554F7061C00EDCD",
            "max_results": 50000,
            "last_appid": 0,
            "include_games": "true",
            "include_dlc": "false"
        }
        
        try:
            # We might need to paginate if > 50k results?
            # Standard GetAppList v2 usually returns everything or truncated.
            # v1 with max_results might need pagination.
            # But for "getting started" let's just fetch the first batch or implement simple loop.
            
            all_apps = []
            
            while True:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                apps = data.get('response', {}).get('apps', [])
                if not apps:
                    break
                    
                all_apps.extend(apps)
                
                # Check pagination logic usually involves 'last_appid'
                # Use the last appid from the current batch for the next request
                if len(apps) < params['max_results']:
                    break
                    
                last_app = apps[-1]
                params['last_appid'] = last_app.get('appid')
                
                print(f"Fetched {len(all_apps)} apps so far...")
                time.sleep(1) # Be nice
                
            return all_apps
            
        except Exception as e:
            print(f"Error fetching all games list: {e}")
            return None

