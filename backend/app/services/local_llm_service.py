import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict
import time

class LocalLLMService:
    # Singleton storage
    _shared_model = None
    _shared_tokenizer = None
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.log_file = "debug_local_llm.log"
        
        with open(self.log_file, "a", encoding='utf-8') as f:
            f.write(f"[Init] LocalLLMService initialized with {model_name} on {self.device} at {time.ctime()}\n")

    def _load_model(self):
        """Lazy load the model only when needed to save resources on startup. Uses Singleton pattern."""
        if LocalLLMService._shared_model is not None:
            return

        print(f"[LocalLLM] Loading model {self.model_name}...")
        with open(self.log_file, "a", encoding='utf-8') as f:
            f.write(f"[Info] Loading model {self.model_name} (Singleton Init)...\n")
            
        try:
            print("[LocalLLM] Loading tokenizer...")
            LocalLLMService._shared_tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            print("[LocalLLM] Tokenizer loaded. Loading model weights (this may take time)...")
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write("[Info] Tokenizer loaded. Loading weights...\n")
            
            if self.device == "cuda":
                LocalLLMService._shared_model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
            else:
                # CPU: Avoid device_map="auto" to prevent "offload to disk" error on Windows
                LocalLLMService._shared_model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32
                )
                print("[LocalLLM] Model weights loaded. Moving to device...")
                with open(self.log_file, "a", encoding='utf-8') as f:
                     f.write("[Info] Weights loaded. Moving to device...\n")
                LocalLLMService._shared_model.to(self.device)
                
            print(f"[LocalLLM] Model loaded successfully on {self.device}")
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(f"[Success] Model loaded on {self.device}\n")
        except Exception as e:
            print(f"[LocalLLM] Error loading model: {e}")
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(f"[Error] Failed to load model: {e}\n")
            raise e

    def polish_and_translate_tags(self, tags: List[str]) -> Dict[str, str]:
        """
        Takes a list of English tags and returns a dict mapping {original: "Thai (Explanation)"}
        """
        if not tags:
            return {}

        self._load_model()
        
        # Prepare prompt (Optimized for 0.5B model - Version 4 - Anti-Chinese/Hallucination)
        tags_str = ", ".join(tags)
        system_prompt = "You are a professional game Localization QA. Translate English game tags to Thai."
        
        user_prompt = f"""Task: Translate these game tags to Thai.
Constraints:
1. Translate to Thai ONLY. Do NOT use Chinese characters (No "服务器", "账号").
2. Use Gamer Slang (e.g. Story Mode -> โหมดเนื้อเรื่อง).
3. If unsure, transliterate to Thai (e.g. Server -> เซิร์ฟเวอร์).
4. Do not make up random words.

Format: [ {{"Original": "Tag", "Translation": "Thai"}} ]

Input: {tags_str}
Output:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        text = LocalLLMService._shared_tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        model_inputs = LocalLLMService._shared_tokenizer([text], return_tensors="pt").to(self.device)

        import time
        start_time = time.time()
        with open(self.log_file, "a", encoding='utf-8') as f:
            f.write(f"[Debug] Starting generation at {start_time}...\n")

        generated_ids = LocalLLMService._shared_model.generate(
            model_inputs.input_ids,
            max_new_tokens=256,
            temperature=0.1, # Reduced to prevent hallucinations
            top_p=0.9
        )
        
        end_time = time.time()
        with open(self.log_file, "a", encoding='utf-8') as f:
            f.write(f"[Debug] Generation finished in {end_time - start_time:.2f} seconds\n")

        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = LocalLLMService._shared_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Log response content for debugging
        with open(self.log_file, "a", encoding='utf-8') as f:
            f.write(f"[Debug] Raw LLM Response: {response}\n")

        # Parse JSON from response
        import json
        import re
        
        try:
            # Extract JSON part (support both Object {} and Array [])
            json_match = re.search(r'(\{|\[).*(\}|\])', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                
                # Handle List format (Model 0.5B tends to output this)
                if isinstance(result, list):
                    normalized_result = {}
                    for item in result:
                        if isinstance(item, dict):
                            # Try to find key/value pair
                            key = item.get("Original") or item.get("original") or list(item.keys())[0]
                            val = item.get("Translation") or item.get("translation") or list(item.values())[0]
                            if key and val:
                                normalized_result[key] = val
                    return normalized_result
                
                return result
            else:
                print(f"[LocalLLM] Could not find JSON in response: {response}")
                return {tag: tag for tag in tags} # Fallback
        except Exception as e:
            print(f"[LocalLLM] Error parsing JSON: {e}")
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(f"[Error] JSON Parse error: {e}\nResponse was: {response}\n")
            return {tag: tag for tag in tags}
