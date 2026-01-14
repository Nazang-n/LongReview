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
        
        # 1. Sample reviews to fit Context Window and avoid rate limits
        # Increased: 10 Pos + 10 Neg (Total 20) for better accuracy
        # Truncate each review to max 400 chars to get more context
        
        sample_pos = [r[:400] for r in positive_reviews[:10]]
        sample_neg = [r[:400] for r in negative_reviews[:10]]
        
        system_prompt = "You are a Senior Game Reviewer. Summarize the pros and cons of a game based on user reviews."
        
        user_prompt = f"""Task: Read these reviews CAREFULLY and extract the Top 5 most frequently mentioned UNIQUE topics for PROS and CONS in Thai.

POSITIVE REVIEWS:
{json.dumps(sample_pos)}

NEGATIVE REVIEWS:
{json.dumps(sample_neg)}

CRITICAL INSTRUCTIONS - READ CAREFULLY:

1. EXTRACT ACTUAL WORDS FROM REVIEWS - Don't summarize, QUOTE what players say:
   * Look for specific nouns, game modes, character names, mechanics that players mention
   * CRITICAL: Quote the EXACT adjectives/descriptors players use:
     - If reviews say "realistic graphics" → "กราฟิกสมจริง" (NOT "กราฟิกสไตล์อนิเมะ")
     - If reviews say "anime art style" → "กราฟิกสไตล์อนิเมะ" (NOT "กราฟิกสวย")
     - If reviews say "hand-drawn art" → "ภาพวาดมือ" (NOT just "กราฟิกดี")
   * Examples of correct extraction:
     - Review: "building system is fun" → Tag: "ระบบสร้างสนุก" ✅
     - Review: "the cat is cute" → Tag: "แมวน่ารัก" ✅
     - Review: "parkour feels smooth" → Tag: "ปาร์คัวร์ลื่นไหล" ✅
   * DO NOT make assumptions - if reviews say "beautiful graphics", find out WHAT KIND:
     - Look for words like: realistic, anime, cartoon, pixel art, hand-drawn, cel-shaded
     - If no specific style mentioned, use "กราฟิกสวย" but PREFER specific styles

2. PRIORITIZE UNIQUENESS - What makes THIS game DIFFERENT from others:
   * FORBIDDEN generic tags (these are BANNED): "เล่นสนุก", "กราฟิกสวย", "เนื้อเรื่องดี", "ควบคุมดี", "เพลงเพราะ"
   * REQUIRED: Look for proper nouns, game modes, specific mechanics:
     ✓ Character names: "แมวน่ารัก", "โจ๊กเกอร์เจ๋ง", "วิลเลนน่ากลัว"
     ✓ Game modes: "โหมดสร้างสรรค์", "โหมดเอาชีวิตรอด", "แบทเทิลรอยัล"
     ✓ Mechanics: "ระบบคราฟ", "ปาร์คัวร์", "ต่อสู้แบบเทิร์น", "สร้างบ้าน"
     ✓ Features: "เล่นกับเพื่อน 4 คน", "มีสกินเยอะ", "มีโหมดออนไลน์"

3. SPECIFICITY EXAMPLES - Good vs Bad:
   ❌ BAD (too generic): "ตัวละครดี" → ✅ GOOD: "ตัวละครมีบุคลิก"
   ❌ BAD: "เกมเพลย์สนุก" → ✅ GOOD: "ระบบต่อสู้สนุก" or "ปริศนาท้าทาย"
   ❌ BAD: "กราฟิกสวย" → ✅ GOOD: "กราฟิกสไตล์อนิเมะ" or "ภาพวาดมือสวย"
   ❌ BAD: "มีเนื้อหา" → ✅ GOOD: "มีด่าน 100 ด่าน" or "มีโหมดเยอะ"

4. NO VAGUE WORDS - Be concrete:
   * Instead of "มีเมม" → "มีมีมตลก" or "ชุมชนสร้างมีม"
   * Instead of "ไม่มีการดูแล" → "ไม่มีอัปเดต" or "ไม่แก้บั๊ก"
   * Instead of "ไม่มีชาร์ม" → "ตัวละครน่าเบื่อ" or "ไม่มีเอกลักษณ์"

5. TRANSLATE GAMING TERMS - Do NOT transliterate, TRANSLATE to Thai meaning:
   * "cheat/cheater/hacker" → "โกง" or "คนโกง" or "โปรโกง" (NEVER "เชท" or "แฮกเกอร์")
   * "grind/grinding" → "ฟาร์ม" or "เก็บเลเวล" (NEVER "ไกรน์")
   * "lag/laggy" → "แลค" or "กระตุก" (OK to use "แลค")
   * "bug/buggy" → "บั๊ก" (OK to use "บั๊ก")
   * "pay to win" → "pay to win" or "จ่ายเงินชนะ" (both OK)
   * "toxic community" → "ชุมชนแย่" or "คนพูดจาแย่" (NEVER "ท็อกซิก")

5. FORBIDDEN NATIONALITY TAGS:
   * NEVER: "รัสเซียมาก", "จีนเยอะ", "ไทยน้อย"
   * Instead: "ภาษาไม่รู้เรื่อง", "สื่อสารยาก", "หาทีมยาก"

6. CONFLICT RESOLUTION:
   * If "เรื่องราวดี" AND "เรื่องราวไม่ดี" both appear, count which is mentioned MORE
   * ONLY include the dominant one

7. FORMAT RULES:
   * Keep tags 2-4 words maximum
   * Use casual Thai gamer language
   * Negative tags must be actual PROBLEMS, not positive statements
   * Return ONLY valid JSON

Format:
{{
  "positive": ["Unique Tag 1", "Unique Tag 2", "Unique Tag 3", "Unique Tag 4", "Unique Tag 5"],
  "negative": ["Specific Problem 1", "Specific Problem 2", "Specific Problem 3", "Specific Problem 4", "Specific Problem 5"]
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
            
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            
            # Check if it's a rate limit error
            if "429" in error_msg or "Too Many Requests" in error_msg:
                self._log(f"[Error] Rate limit exceeded after {elapsed:.2f}s. Please wait a few minutes before trying again.")
                return {"positive": [], "negative": []}
            else:
                self._log(f"[Error] Summarization failed after {elapsed:.2f}s: {error_msg}")
                return {"positive": [], "negative": []}
            
        try:
            
            # --- SANITIZATION STEP (Copy from polish_and_translate_tags) ---
            import re
            def sanitize_text(text):
                # 1. Hard Replacements (Fixes Stubborn AI glitches)
                text = text.replace("obile", "มือถือ") # Fix "ไม่เหมาะสมobile"
                text = text.replace("ปาร์รี่", "ปัดป้อง") # Fix "Parry" transliteration
                text = text.replace("แปรี่", "ปัดป้อง")
                text = text.replace("ปิดดิ้ง", "บิลด์") # Fix "Building" transliteration
                text = text.replace("ปัดดิ้ง", "บิลด์") # Fix "Building" transliteration
                
                # 2. Regex Filter
                # Allow Thai, English, Numbers, spaces, and basic punctuation
                cleaned = re.sub(r'[^\u0E00-\u0E7F a-zA-Z0-9\.\-\(\)\,]', '', text)
                return cleaned.strip()

            # Helper function to check if tag is complete (not ending with connecting words)
            def is_complete_tag(tag):
                incomplete_endings = ['และ', 'หรือ', 'กับ', 'ที่', 'ของ', 'ใน', 'ไป', 'มา']
                return not any(tag.endswith(ending) for ending in incomplete_endings)

            final_json = {"positive": [], "negative": []}
            
            for tag in result_json.get("positive", []):
                clean_tag = sanitize_text(tag)
                if clean_tag and is_complete_tag(clean_tag):
                    final_json["positive"].append(clean_tag)
                elif clean_tag:
                    self._log(f"[Incomplete] Skipped incomplete tag: '{clean_tag}'")
                
            for tag in result_json.get("negative", []):
                clean_tag = sanitize_text(tag)
                if clean_tag and is_complete_tag(clean_tag):
                    final_json["negative"].append(clean_tag)
                elif clean_tag:
                    self._log(f"[Incomplete] Skipped incomplete tag: '{clean_tag}'")
            
            
            
            
            # --- CONFLICT DETECTION & REMOVAL ---
            # This feature detects opposite-meaning tags and removes conflicts based on review counts
            # Example: If "เบาเครื่อง" (positive) and "กินสเปค" (negative) both appear,
            # it keeps the tag from the side with MORE reviews
            
            # Define opposite-meaning tag pairs (Thai)
            conflicting_pairs = [
                ("เนื้อหาเยอะ", "เนื้อหาน้อย"),
                ("เบาเครื่อง", "กินสเปค"),
                ("กราฟฟิกสวย", "กราฟฟิกแย่"),
                ("กราฟฟิกดี", "กราฟฟิกแย่"),
                ("ควบคุมง่าย", "ควบคุมยาก"),
                ("ง่ายเกินไป", "ยากเกินไป"),
                ("เล่นง่าย", "เล่นยาก"),
                ("ราคาถูก", "ราคาแพง"),
                ("สนุก", "น่าเบื่อ"),
                ("เพลงเพราะ", "เพลงแย่"),
                # Character-related conflicts
                ("ตัวละครน่าสนใจ", "ตัวละครไม่"),
                ("ตัวละครดี", "ตัวละครไม่"),
                ("ตัวละคร", "ตัวละครไม่"),
                # Story-related conflicts
                ("เรื่องราวดี", "เรื่องราวไม่"),
                ("เรื่องราวน่าสนใจ", "เรื่องราวไม่"),
                ("เรื่องราว", "เรื่องราวไม่"),
                # Update-related conflicts (comprehensive)
                ("อัปเดต", "ไม่มีอัปเดต"),
                ("อัปเดต", "ไม่อัปเดต"),
                ("อัปเดต", "ไม่มีการอัปเดต"),
                ("ปรับปรุง", "ไม่มีอัปเดต"),
                ("ปรับปรุง", "ไม่อัปเดต"),
                ("ปรับปรุง", "ไม่มีการอัปเดต"),
                # Development-related conflicts (NEW)
                ("อัปเดตเกม", "ไม่มีการพัฒนา"),
                ("พัฒนา", "ไม่มีการพัฒนา"),
                ("พัฒนา", "ไม่พัฒนา"),
                ("อัปเดต", "ไม่มีการพัฒนา"),
                # Player population conflicts (NEW)
                ("มีคนเล่น", "คนเล่นน้อย"),
                ("ผู้เล่นเยอะ", "คนเล่นน้อย"),
                ("ชุมชนใหญ่", "คนเล่นน้อย"),
                ("มีคนเล่น", "ผู้เล่นน้อย"),
                # Other conflicts
                ("เพิ่มเนื้อหา", "ไม่มีเนื้อหาใหม่"),
                ("ปรับแต่งได้ดี", "กินสเปค"),
                ("เนื้อเรื่องดี", "เนื้อเรื่องแย่"),
                ("มัลติเพลเยอร์สนุก", "มัลติเพลเยอร์แย่"),
                ("ไม่ pay to win", "pay to win"),
                ("เซิร์ฟเวอร์เสถียร", "เซิร์ฟเวอร์กระตุก"),
                ("หลากหลาย", "น้อย"),
            ]
            
            # Compare review counts to decide which tag to keep
            positive_review_count = len(positive_reviews)
            negative_review_count = len(negative_reviews)
            
            positive_tags = final_json["positive"]
            negative_tags = final_json["negative"]
            
            # Debug: Log all tags before conflict detection
            self._log(f"[Conflict Debug] Positive tags: {positive_tags}")
            self._log(f"[Conflict Debug] Negative tags: {negative_tags}")
            
            tags_to_remove_from_positive = []
            tags_to_remove_from_negative = []
            
            for pos_tag, neg_tag in conflicting_pairs:
                # Check if both tags exist
                pos_exists = any(pos_tag in tag for tag in positive_tags)
                neg_exists = any(neg_tag in tag for tag in negative_tags)
                
                if pos_exists and neg_exists:
                    # Compare review counts - keep the tag from the side with MORE reviews
                    if positive_review_count > negative_review_count:
                        # Only remove if the conflict keyword is a significant part of the tag
                        for tag in negative_tags:
                            if neg_tag in tag and len(neg_tag) / len(tag) > 0.4:  # At least 40% of tag
                                tags_to_remove_from_negative.append(tag)
                                self._log(f"[Conflict] Removed '{tag}' from negative (contains '{neg_tag}', pos_reviews={positive_review_count} > neg_reviews={negative_review_count})")
                    else:
                        for tag in positive_tags:
                            if pos_tag in tag and len(pos_tag) / len(tag) > 0.4:
                                tags_to_remove_from_positive.append(tag)
                                self._log(f"[Conflict] Removed '{tag}' from positive (contains '{pos_tag}', neg_reviews={negative_review_count} >= pos_reviews={positive_review_count})")
                
                # Also check reverse (negative tag in positive, positive tag in negative)
                neg_in_pos = any(neg_tag in tag for tag in positive_tags)
                pos_in_neg = any(pos_tag in tag for tag in negative_tags)
                
                if neg_in_pos and pos_in_neg:
                    # Same logic - compare review counts
                    if positive_review_count > negative_review_count:
                        for tag in negative_tags:
                            if pos_tag in tag and len(pos_tag) / len(tag) > 0.4:
                                tags_to_remove_from_negative.append(tag)
                                self._log(f"[Conflict] Removed '{tag}' from negative (contains '{pos_tag}', pos_reviews={positive_review_count} > neg_reviews={negative_review_count})")
                    else:
                        for tag in positive_tags:
                            if neg_tag in tag and len(neg_tag) / len(tag) > 0.4:
                                tags_to_remove_from_positive.append(tag)
                                self._log(f"[Conflict] Removed '{tag}' from positive (contains '{neg_tag}', neg_reviews={negative_review_count} >= pos_reviews={positive_review_count})")
            
            # Remove conflicting tags from both sides
            final_json["positive"] = [tag for tag in positive_tags if tag not in tags_to_remove_from_positive]
            final_json["negative"] = [tag for tag in negative_tags if tag not in tags_to_remove_from_negative]
            
            
            
            
            return final_json

        except Exception as e:
            self._log(f"[Error] Groq Summarize failed: {str(e)}")
            # Fallback structure
            return {"positive": [], "negative": []}
