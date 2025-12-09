import requests
from typing import Optional, Dict, Any, List
import time


class SteamAPIClient:
    """Client for fetching data from Steam API"""
    
    BASE_URL = "https://store.steampowered.com"
    
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
        
        while True:
            data = SteamAPIClient.get_app_reviews(
                app_id=app_id,
                language=language,
                cursor=cursor
            )
            
            if not data or data.get("success") != 1:
                break
            
            reviews = data.get("reviews", [])
            if not reviews:
                break
            
            all_reviews.extend(reviews)
            
            # Check if we've reached max_reviews
            if max_reviews and len(all_reviews) >= max_reviews:
                all_reviews = all_reviews[:max_reviews]
                break
            
            # Get next cursor for pagination
            cursor = data.get("cursor")
            if not cursor:
                break
            
            # Be nice to Steam API - add small delay
            time.sleep(0.5)
        
        return all_reviews
    
    @staticmethod
    def get_app_details(app_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch app details from Steam
        
        Args:
            app_id: Steam application ID
            
        Returns:
            Dictionary containing app details or None if failed
        """
        url = f"{SteamAPIClient.BASE_URL}/api/appdetails"
        params = {"appids": app_id}
        
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
