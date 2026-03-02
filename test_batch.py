import requests

print("Testing batch import...")
try:
    response = requests.post("http://localhost:8000/api/steam/steamspy/import/batch?limit=5")
    print(response.json())
except Exception as e:
    print(e)
