import requests
from typing import Optional, Dict, Any, List
import time


class SteamAPIClient:
    """Client for fetching data from Steam API"""
    
    BASE_URL = "https://store.steampowered.com"
    STEAMSPY_BASE_URL = "https://steamspy.com/api.php"
    
    @staticmethod
    def get_app_reviews(
        app_id: int,
        language: str = "thai",
        filter_type: str = "all",
        cursor: str = "*",
        num_per_page: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch reviews for a specific Steam app
        
        Args:
            app_id: Steam application ID
            language: Language filter (e.g., 'thai', 'english')
            filter_type: Filter type ('all', 'recent', 'updated')
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
            "cursor": cursor,
            "num_per_page": num_per_page
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Steam reviews: {e}")
            return None
    
    @staticmethod
    def get_all_reviews(
        app_id: int,
        language: str = "thai",
        max_reviews: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all reviews for a Steam app (with pagination)
        
        Args:
            app_id: Steam application ID
            language: Language filter
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
                cursor=cursor
            )
            
            print(f"[DEBUG] Steam API response: success={data.get('success') if data else None}, reviews={len(data.get('reviews', [])) if data else 0}")
            
            if not data or data.get("success") != 1:
                print(f"[WARNING] Steam API failed or returned no data")
                break
            
            reviews = data.get("reviews", [])
            if not reviews:
                print(f"⚠️ No reviews in response")
                break
            
            all_reviews.extend(reviews)
            
            # Check if we actually got new reviews
            if len(all_reviews) == previous_count:
                # No new reviews added, break to prevent infinite loop
                print(f"⚠️ No new reviews fetched, stopping pagination")
                break
            
            # Check if we've reached max_reviews
            if max_reviews and len(all_reviews) >= max_reviews:
                all_reviews = all_reviews[:max_reviews]
                break
            
            # Get next cursor for pagination
            new_cursor = data.get("cursor")
            if not new_cursor or new_cursor == cursor:
                # No more pages or cursor didn't change (prevent infinite loop)
                print(f"🛑 Pagination complete or cursor unchanged")
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
        Fetch newest games by release date from SteamSpy
        
        Args:
            limit: Number of newest games to fetch
            
        Returns:
            List of game dictionaries sorted by release date (newest first)
        """
        all_games = SteamAPIClient.get_all_games_from_steamspy()
        
        if not all_games:
            return None
        
        # Convert to list
        games_list = []
        for app_id, game_data in all_games.items():
            game_data['app_id'] = app_id
            games_list.append(game_data)
        
        # Filter out games without initialprice and convert to int
        games_with_date = []
        for game in games_list:
            initialprice = game.get('initialprice', 0)
            # Convert to int if it's a string
            try:
                if isinstance(initialprice, str):
                    initialprice = int(initialprice)
                if initialprice > 0:
                    game['initialprice_int'] = initialprice
                    games_with_date.append(game)
            except (ValueError, TypeError):
                # Skip games with invalid initialprice
                continue
        
        # Sort by initialprice (Unix timestamp) in descending order (newest first)
        sorted_games = sorted(
            games_with_date,
            key=lambda x: x.get('initialprice_int', 0),
            reverse=True
        )
        
        return sorted_games[:limit]
