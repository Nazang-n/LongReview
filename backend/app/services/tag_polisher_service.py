import os
from google import genai
from typing import List, Dict
import json
import asyncio
import time

class TagPolisherService:
    def __init__(self):
        self.log_file = "debug_tags.log"
        self.api_key = os.getenv("GOOGLE_API_KEY")
        with open(self.log_file, "a", encoding='utf-8') as f:
            f.write(f"[Init] TagPolisherService initialized at {time.ctime()}\n")
            if self.api_key:
                f.write("[Init] API Key found.\n")
            else:
                f.write("[Init] NO API KEY FOUND.\n")

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            # List available models to debug 404 error
            try:
                models = self.client.models.list()
                with open(self.log_file, "a", encoding='utf-8') as f:
                    f.write("[Init] Available models:\n")
                    for m in models:
                        f.write(f"- {m.name}\n")
            except Exception as e:
                with open(self.log_file, "a", encoding='utf-8') as f:
                    f.write(f"[Init] Error listing models: {e}\n")
        else:
            print("[TagPolisher] No GOOGLE_API_KEY found. Skipping AI polishing.")
            self.client = None

    def polish_tags(self, tags: List[str]) -> Dict[str, str]:
        """
        Refines a list of tags to be more readable and professional.
        Example: "los pals" -> "Lost Pals", "lag" -> "Lag Issues"
        
        Args:
            tags: List of raw tag strings
            
        Returns:
            Dictionary mapping {original_tag: polished_tag}
        """
        if not self.client or not tags:
            return {tag: tag for tag in tags}

        try:
            # Construct a clear prompt for the LLM
            prompt = f"""
            You are a Video Game Tag Editor. Your goal is to fix typos and improve the readability of these game review tags without changing their meaning.
            
            Rules:
            1. Fix typos (e.g., "los pals" -> "Lost Pals", "graphix" -> "Graphics").
            2. Make vague negative tags more descriptive (e.g., "save files" -> "Save File Corruption", "wild pals" -> "Wild Pal AI Issues").
            3. Keep well-known terms AS IS (e.g., "Early Access", "Open World", "FPS").
            4. Capitalize properly (Title Case).
            5. Return JSON format strictly: {{ "original_tag": "Polished Tag" }}.
            
            Tags to polish:
            {json.dumps(tags)}
            """
            
            # Retry logic for rate limits
            max_retries = 3
            retry_delay = 2  # seconds
            
            result_text = ""
            
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model='gemini-flash-latest',
                        contents=prompt
                    )
                    result_text = response.text.strip()
                    break # Success
                except Exception as e:
                    error_msg = str(e)
                    if '429' in error_msg or 'quota' in error_msg.lower() or 'detailed' in error_msg.lower(): # 'detailed' covers Resource Exhausted
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            print(f"[TagPolisher] Rate limit hit. Waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                    print(f"[TagPolisher] Attempt {attempt+1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise e

            if not result_text:
                return {tag: tag for tag in tags}

            # Clean up partial JSON codes if any (e.g. ```json ... ```)
            if result_text.startswith("```"):
                result_text = result_text.replace("```json", "").replace("```", "")
                
            polished_map = json.loads(result_text)
            
            # Validation: Ensure all tags are present, fallback to original if missing
            final_map = {}
            for tag in tags:
                final_map[tag] = polished_map.get(tag, tag)
                
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(f"[Success] Mapped {len(final_map)} tags.\n")
            return final_map
            
        except Exception as e:
            print(f"[TagPolisher] Error polishing tags: {e}")
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(f"[Error] Polishing failed: {e}\n")
            
            # --- Fallback Mechanism for known issues ---
            fallback_map = {
                "los pals": "Lost Pals",
                "wild pals": "Wild Pal AI Issues",
                "nothing change": "Lack of Innovation",
                "save files": "Save File Corruption",
                "machine guns": "Machine Guns Balance", 
                "content feels": "Content Feel",
                "core ideas": "Core Concepts",
                "later stages": "Late Game Content",
                "early access": "Early Access",
                "open world survival": "Open World Survival",
                "new pals": "New Pals",
                "creature collecting": "Creature Collecting",
                "world settings": "World Settings"
            }
            
            # Use fallback map where possible, otherwise keep original
            final_fallback = {}
            for tag in tags:
                lower_tag = tag.lower()
                if lower_tag in fallback_map:
                    final_fallback[tag] = fallback_map[lower_tag]
                else:
                    final_fallback[tag] = tag.title() # Simple Title Case fallback

            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(f"[Fallback] Applied backup dictionary to {len(tags)} tags.\n")
                
            return final_fallback
