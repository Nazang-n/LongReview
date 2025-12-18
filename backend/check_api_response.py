"""Check raw API response structure"""
import asyncio
import httpx
import json
from app.config.settings import settings

async def check_api():
    params = {
        "apikey": settings.NEWSDATA_API_KEY,
        "q": settings.NEWSDATA_QUERY
    }
    
    # Only add country if specified
    if settings.NEWSDATA_COUNTRY:
        params["country"] = settings.NEWSDATA_COUNTRY
    
    # Only add language if specified
    if settings.NEWSDATA_LANGUAGE:
        params["language"] = settings.NEWSDATA_LANGUAGE
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            settings.NEWSDATA_API_URL,
            params=params,
            timeout=10.0
        )
        data = response.json()
        
        # Save full JSON response
        with open('api_full_response.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("Full API response saved to api_full_response.json")
        
        # Also print first article description
        if "results" in data and len(data["results"]) > 0:
            first = data["results"][0]
            print(f"\nFirst article title: {first.get('title', 'N/A')}")
            print(f"Description: {first.get('description', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(check_api())
