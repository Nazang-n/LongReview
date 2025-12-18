"""
AI Translation Helper using Google Gemini (New API)
"""
import os
from typing import Optional
from google import genai
from google.genai import types
from langdetect import detect, LangDetectException


class AITranslator:
    """Helper class for AI-powered translation"""
    
    def __init__(self):
        # Get API key from environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            print("Warning: GEMINI_API_KEY not found. AI translation will be disabled.")
            self.client = None
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text
        
        Args:
            text: Text to detect language
            
        Returns:
            Language code ('en', 'th', etc.) or None if failed
        """
        if not text or len(text.strip()) < 3:
            return None
            
        try:
            return detect(text)
        except LangDetectException:
            return None
    
    def translate_to_thai(self, text: str) -> str:
        """
        Translate English text to Thai using AI
        
        Args:
            text: English text to translate
            
        Returns:
            Thai translation or original text if translation fails
        """
        if not self.client:
            print("⚠️ Warning: Gemini API not configured. Translation disabled.")
            return text
        
        if not text or len(text.strip()) < 3:
            return text
        
        # Check if text contains Thai characters
        has_thai = any('\u0E00' <= char <= '\u0E7F' for char in text)
        
        # Check language with langdetect
        lang = self.detect_language(text)
        print(f"🔍 Detected language: {lang}, Has Thai chars: {has_thai} for text: {text[:50]}...")
        
        # If has Thai characters or detected as Thai, skip translation
        if has_thai or lang == 'th':
            print("✅ Already in Thai, skipping translation")
            return text
        
        # Retry logic for rate limits
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"🤖 Translating to Thai... (attempt {attempt + 1}/{max_retries})")
                prompt = f"""แปลข้อความต่อไปนี้เป็นภาษาไทยที่เป็นธรรมชาติและเหมาะสมสำหรับคำอธิบายเกม:

"{text}"

ให้แปลเป็นภาษาไทยที่อ่านง่าย เป็นธรรมชาติ และเหมาะสมกับบริบทของเกม ไม่ต้องใส่คำอธิบายเพิ่มเติม แค่ข้อความที่แปลแล้วเท่านั้น"""
                
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=prompt
                )
                
                translated = response.text.strip()
                
                # Remove quotes if present
                if translated.startswith('"') and translated.endswith('"'):
                    translated = translated[1:-1]
                if translated.startswith("'") and translated.endswith("'"):
                    translated = translated[1:-1]
                
                print(f"✅ Translation successful: {translated[:50]}...")
                return translated
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"⏳ Rate limit hit. Waiting {wait_time}s before retry...")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Rate limit exceeded after {max_retries} attempts. Using original text.")
                        return text
                else:
                    print(f"❌ AI translation error: {e}")
                    return text
        
        return text
    
    def get_thai_description(self, thai_desc: Optional[str], english_desc: Optional[str]) -> Optional[str]:
        """
        Get Thai description, translating from English if needed
        
        Args:
            thai_desc: Description from Thai API
            english_desc: Description from English API (fallback)
            
        Returns:
            Thai description (original or translated)
        """
        # If Thai description exists and is actually in Thai, use it
        if thai_desc and len(thai_desc.strip()) > 3:
            lang = self.detect_language(thai_desc)
            if lang == 'th':
                return thai_desc
        
        # If Thai description is in English or doesn't exist, translate English version
        if english_desc and len(english_desc.strip()) > 3:
            lang = self.detect_language(english_desc)
            if lang == 'en':
                return self.translate_to_thai(english_desc)
            elif lang == 'th':
                return english_desc
        
        # Fallback to whatever we have
        return thai_desc or english_desc


# Global translator instance
translator = AITranslator()
