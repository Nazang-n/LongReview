import sys
import os

# Add backend to path so we can import app modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.services.local_llm_service import LocalLLMService

def test_llm():
    print("Initializing LocalLLMService...")
    service = LocalLLMService()
    
    test_tags = ["Roguelike", "FPS", "Open World", "Early Access", "Co-op"]
    print(f"Testing with tags: {test_tags}")
    
    try:
        print("Calling polish_and_translate_tags (this will load the model)...")
        result = service.polish_and_translate_tags(test_tags)
        
        print("\n--- Result ---")
        for original, translated in result.items():
            print(f"{original} -> {translated}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_llm()
