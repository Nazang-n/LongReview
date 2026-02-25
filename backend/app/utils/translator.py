"""
AI Translation Helper using Google Gemini (New API) with Google Translate fallback
"""
import os
from typing import Optional
from google import genai
from google.genai import types
from langdetect import detect, LangDetectException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Google Translate as fallback
try:
    from deep_translator import GoogleTranslator
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False
    print("WARNING: deep-translator not available. Install with: pip install deep-translator")


class AITranslator:
    """Helper class for AI-powered translation with Google Translate fallback"""
    
    def __init__(self):
        # Get API key from environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
            print("Gemini AI translator initialized")
        else:
            print("WARNING: GEMINI_API_KEY not found. AI translation will be disabled.")
            self.client = None
        
        # Initialize Google Translate fallback
        if GOOGLE_TRANSLATE_AVAILABLE:
            self.google_translator = GoogleTranslator(source='en', target='th')
            print("Google Translate fallback initialized")
        else:
            self.google_translator = None
    
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
    
    def translate_with_google(self, text: str) -> Optional[str]:
        """
        Translate text to Thai using Google Translate (fallback)
        
        Args:
            text: Text to translate
            
        Returns:
            Thai translation or None if failed
        """
        if not self.google_translator:
            return None
        
        try:
            # Chunking logic for long texts
            if len(text) > 4900:
                print(f"Text too long ({len(text)} chars). Chunking for Google Translate...")
                chunks = []
                current_chunk = ""
                # Simple split by paragraphs to preserve context
                paragraphs = text.split('\n')
                for para in paragraphs:
                    if len(current_chunk) + len(para) < 4500:
                        current_chunk += para + "\n"
                    else:
                        chunks.append(current_chunk)
                        current_chunk = para + "\n"
                if current_chunk:
                    chunks.append(current_chunk)
                
                translated_chunks = []
                for chunk in chunks:
                    if not chunk.strip():
                        translated_chunks.append("")
                        continue
                        
                    res = self.google_translator.translate(chunk)
                    if res:
                        translated_chunks.append(res)
                    else:
                        translated_chunks.append(chunk) # Fallback to original
                
                full_translation = "\n".join(translated_chunks)
                print("Translation successful (chunked)")
                return full_translation

            print("Using Google Translate fallback...")
            result = self.google_translator.translate(text)
            if result:
                try:
                    print(f"Google Translate successful: {result[:50]}...")
                except UnicodeEncodeError:
                    print("Google Translate successful (Thai text)")
                return result
        except Exception as e:
            try:
                print(f"Google Translate error: {e}")
            except UnicodeEncodeError:
                print("Google Translate error (encoding issue)")
        
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
            print("WARNING: Gemini API not configured. Trying Google Translate...")
            google_result = self.translate_with_google(text)
            if google_result:
                return google_result
            return text
        
        if not text or len(text.strip()) < 3:
            return text
        
        # Check if text contains Thai characters
        has_thai = any('\u0E00' <= char <= '\u0E7F' for char in text)
        
        # Check language with langdetect
        lang = self.detect_language(text)
        print(f"Detected language: {lang}, Has Thai chars: {has_thai} for text: {text[:50]}...")
        
        # If has Thai characters or detected as Thai, skip translation
        if has_thai or lang == 'th':
            print("Already in Thai, skipping translation")
            return text
        
        # Retry logic for rate limits
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"Translating to Thai... (attempt {attempt + 1}/{max_retries})")
                prompt = f"""แปลข้อความต่อไปนี้เป็นภาษาไทยที่เป็นธรรมชาติและเหมาะสมสำหรับคำอธิบายเกม:

"{text}"

ให้แปลเป็นภาษาไทยที่อ่านง่าย เป็นธรรมชาติ และเหมาะสมกับบริบทของเกม ไม่ต้องใส่คำอธิบายเพิ่มเติม แค่ข้อความที่แปลแล้วเท่านั้น"""
                
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt
                )
                
                translated = response.text.strip()
                
                # Remove quotes if present
                if translated.startswith('"') and translated.endswith('"'):
                    translated = translated[1:-1]
                if translated.startswith("'") and translated.endswith("'"):
                    translated = translated[1:-1]
                
                print(f"Translation successful: {translated[:50]}...")
                return translated
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"Rate limit hit. Waiting {wait_time}s before retry...")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"ERROR: Rate limit exceeded after {max_retries} attempts.")
                        # Try Google Translate fallback
                        google_result = self.translate_with_google(text)
                        if google_result:
                            return google_result
                        return text
                else:
                    print(f"ERROR: AI translation error: {e}")
                    # Try Google Translate fallback for any error
                    google_result = self.translate_with_google(text)
                    if google_result:
                        return google_result
                    return text
        
        # If all retries failed, try Google Translate
        google_result = self.translate_with_google(text)
        if google_result:
            return google_result
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
