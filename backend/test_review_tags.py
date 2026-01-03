"""
Test script for review tags API
"""
import requests

# Test with game ID 727 (should have Thai reviews)
game_id = 727
base_url = "http://localhost:8000"

print(f"Testing Review Tags API for game {game_id}...")
print("=" * 60)

# Test 1: Generate tags (force refresh)
print("\n1. Generating tags (force refresh)...")
response = requests.post(f"{base_url}/api/games/{game_id}/review-tags/refresh")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Success: {data.get('success')}")
    print(f"Total reviews analyzed: {data.get('total_reviews_analyzed')}")
    print(f"Positive reviews: {data.get('positive_reviews')}")
    print(f"Negative reviews: {data.get('negative_reviews')}")
    
    print("\nPositive Tags:")
    for tag in data.get('positive_tags', [])[:5]:
        print(f"  - {tag['word']}: {tag['count']}")
    
    print("\nNegative Tags:")
    for tag in data.get('negative_tags', [])[:5]:
        print(f"  - {tag['word']}: {tag['count']}")
else:
    print(f"Error: {response.text}")

# Test 2: Get tags (from cache)
print("\n" + "=" * 60)
print("\n2. Getting tags (from cache)...")
response = requests.get(f"{base_url}/api/games/{game_id}/review-tags")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Success: {data.get('success')}")
    print(f"Total tags: {data.get('total_tags')}")
    print(f"Last updated: {data.get('last_updated')}")
    
    print("\nPositive Tags:")
    for tag in data.get('positive_tags', [])[:5]:
        print(f"  - {tag['tag']}: {tag['count']}")
    
    print("\nNegative Tags:")
    for tag in data.get('negative_tags', [])[:5]:
        print(f"  - {tag['tag']}: {tag['count']}")
else:
    print(f"Error: {response.text}")

print("\n" + "=" * 60)
print("Test completed!")
