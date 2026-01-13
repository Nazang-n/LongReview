import os
import json
import time
from groq import Groq

# API Key provided by user (Fallback if not in env)
DEFAULT_KEY = "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"

class GroqService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GroqService, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.log_file = "debug_groq.log"
        return cls._instance

    def __init__(self):
        if self.client is None:
            api_key = os.getenv("GROQ_API_KEY", DEFAULT_KEY)
            self.client = Groq(api_key=api_key)
            self._log(f"[Init] GroqService initialized with key ending in ...{api_key[-4:]}")

    def _log(self, message):
        """Write logs to file."""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")

    def polish_and_translate_tags(self, tags: list) -> dict:
        """
        Translates a list of English tags to Thai using Groq (Llama3-70b-8192).
        Returns a dictionary mapping { 'Original': 'Thai Translation' }
        """
        if not tags:
            return {}
            
        tags_str = ", ".join(tags)
        self._log(f"[Info] Requesting translation for {len(tags)} tags: {tags}")
        
        system_prompt = "You are a professional game Localization QA. Translate English game tags to Thai."
        
        user_prompt = f"""Task: Translate these game tags to Thai.
Constraints:
1. Translate to Thai ONLY. Do NOT use Chinese, Japanese, or Korean characters (No '服务器', 'セーブ').
2. Correct English typos BEFORE translating (e.g. 'Raid Bos' -> 'Raid Boss').
3. Use Gamer Slang (e.g. Story Mode -> โหมดเนื้อเรื่อง, Open World -> โลกเปิด, Raid Boss -> เรดบอส).
4. Translate descriptive terms (Survival, Building, Crafting) into Thai meanings (e.g. เอาชีวิตรอด, สร้างฐาน).
5. Only transliterate specific Proper Nouns or Tech terms (e.g. Server -> เซิร์ฟเวอร์).
5. Do not make up random words.
6. Return ONLY valid JSON format.

Format: {{ "Original_Tag": "Thai_Translation", ... }}

Input: {tags_str}
Output JSON:"""

        start_time = time.time()
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                model="llama-3.3-70b-versatile", # Update to latest supported model
                temperature=0.3,
                max_tokens=1024,
                top_p=1,
                stream=False,
                response_format={"type": "json_object"}, 
            )
            
            elapsed = time.time() - start_time
            result_content = chat_completion.choices[0].message.content
            self._log(f"[Success] Generated in {elapsed:.2f}s. Response: {result_content}")
            
            import json
            parsed_result = json.loads(result_content)
            
            # Normalize keys to match input exactly if possible, though Dict format is flexible
            # Creating a cleaned map
            final_map = {}
            for tag in tags:
                # Try to find the translation in the result (case-insensitive fallback)
                if tag in parsed_result:
                    final_map[tag] = parsed_result[tag]
                else:
                    # Search case-insensitive
                    found = False
                    for k, v in parsed_result.items():
                        if k.lower() == tag.lower():
                            final_map[tag] = v
                            found = True
                            break
                    if not found:
                        final_map[tag] = tag # Fallback to original

            # --- SANITIZATION STEP ---
            # Remove any characters that are NOT Thai, English, Numbers, or basic punctuation.
            # This kills Chinese/Japanese charcters (e.g. 襲撃, セーブ) definitively.
            import re
            def sanitize_text(text):
                # Allow Thai, English, Numbers, spaces, and basic punctuation
                # Unicode ranges:
                # Thai: \u0E00-\u0E7F
                # English: a-zA-Z
                # Numbers: 0-9
                # Punctuation: \s\.\-\(\)\,
                cleaned = re.sub(r'[^\u0E00-\u0E7F a-zA-Z0-9\.\-\(\)\,]', '', text)
                return cleaned.strip()

            for k, v in final_map.items():
                original_val = v
                final_map[k] = sanitize_text(v)
                if original_val != final_map[k]:
                    self._log(f"[Sanitized] '{original_val}' -> '{final_map[k]}'")
            
            return final_map

        except Exception as e:
            self._log(f"[Error] Groq API failed: {str(e)}")
            return {tag: tag for tag in tags} # Fallback to no translation

    def summarize_reviews(self, positive_reviews: list, negative_reviews: list) -> dict:
        """
        Directly analyzes raw reviews and extracts Top 5 Pros & Cons in Thai.
        Bypasses the Dictionary/NLP keyword extraction.
        """
        import json
        
        # 1. Sample reviews to fit Context Window (approx 6k tokens safe for Llama3-70b)
        # Optimized: 10 Pos + 10 Neg (Total 20) to stay under Rate Limit (12k TPM)
        # Truncate each review to max 500 chars to be safe.
        
        sample_pos = [r[:500] for r in positive_reviews[:10]]
        sample_neg = [r[:500] for r in negative_reviews[:10]]
        
        system_prompt = "You are a Senior Game Reviewer. Summarize the pros and cons of a game based on user reviews."
        
        user_prompt = f"""Task: Read these reviews and summarize the Top 5 PROS and Top 5 CONS in Thai.
        
POSITIVE REVIEWS:
{json.dumps(sample_pos)}

NEGATIVE REVIEWS:
{json.dumps(sample_neg)}

        Instructions:
        1. Identify the most frequent but **SPECIFIC** topics.
        2. **KEEP IT SHORT (2-4 Words Max)!** No full sentences.
           - BAD: "กินทรัพยากรเครื่องคอมพิวเตอร์มาก" (Too long)
           - GOOD: "กินสเปค" (Short & Punchy)
           - BAD: "มีเพื่อนคู่หูที่น่ารัก"
           - GOOD: "แมวน่ารัก"
        3. Use Gamer Slang:
           - Resources/Performance -> กินสเปค / เบาเครื่อง
           - Cheater -> โปรโกง
           - Mobile -> มือถือ
           - Microtransactions -> เติมเงิน / กาชา
        4. Focus on Unique Mechanics but keep it concise.
        5. Return JSON format ONLY.
        
        Format:
        {{
          "positive": ["Tag 1", "Tag 2", "Tag 3", "Tag 4", "Tag 5"],
          "negative": ["Tag 1", "Tag 2", "Tag 3", "Tag 4", "Tag 5"]
        }}
        
        Output JSON:"""

        start_time = time.time()
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3, 
                max_tokens=1024,
                top_p=1,
                stream=False,
                response_format={"type": "json_object"}, 
            )
            
            elapsed = time.time() - start_time
            result_content = chat_completion.choices[0].message.content
            self._log(f"[Success] Summarized in {elapsed:.2f}s. Response: {result_content}")
            
            result_json = json.loads(result_content)
            
            # --- SANITIZATION STEP (Copy from polish_and_translate_tags) ---
            import re
            def sanitize_text(text):
                # 1. Hard Replacements (Fixes Stubborn AI glitches)
                text = text.replace("obile", "มือถือ") # Fix "ไม่เหมาะสมobile"
                text = text.replace("ปาร์รี่", "ปัดป้อง") # Fix "Parry" transliteration
                text = text.replace("แปรี่", "ปัดป้อง")
                
                # 2. Regex Filter
                # Allow Thai, English, Numbers, spaces, and basic punctuation
                cleaned = re.sub(r'[^\u0E00-\u0E7F a-zA-Z0-9\.\-\(\)\,]', '', text)
                return cleaned.strip()

            final_json = {"positive": [], "negative": []}
            
            for tag in result_json.get("positive", []):
                clean_tag = sanitize_text(tag)
                if clean_tag: final_json["positive"].append(clean_tag)
                
            for tag in result_json.get("negative", []):
                clean_tag = sanitize_text(tag)
                if clean_tag: final_json["negative"].append(clean_tag)
            
            return final_json

        except Exception as e:
            self._log(f"[Error] Groq Summarize failed: {str(e)}")
            # Fallback structure
            return {"positive": [], "negative": []}
