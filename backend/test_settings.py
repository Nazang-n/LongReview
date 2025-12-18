"""
Quick test to check what settings are loaded
"""
from app.config.settings import settings

print("=" * 50)
print("LOADED SETTINGS:")
print("=" * 50)
print(f"NEWSDATA_API_KEY: {settings.NEWSDATA_API_KEY}")
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"PORT: {settings.PORT}")
print("=" * 50)
