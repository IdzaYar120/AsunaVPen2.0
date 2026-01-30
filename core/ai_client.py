import logging
import google.generativeai as genai
from config.settings import Settings

class AIClient:
    def __init__(self):
        self.model = None
        self.chat = None
        self.is_ready = False
        self.logger = logging.getLogger("AIClient")

    def init_ai(self, api_key):
        if not api_key:
            self.logger.warning("API Key missing.")
            return False
            
        try:
            genai.configure(api_key=api_key)
            
            # System Prompt (Persona - Asuna Yuuki)
            system_prompt = """You are Asuna Yuuki (from Sword Art Online), a virtual companion on the user's desktop.
            Language: Ukrainian (speak naturally, cutely).
            Personality: Gentle, caring, mature but sometimes playful. You are the 'Sub-leader' type - organized but sweet.
            
            Key Traits:
            - You deeply care about the user (treat them like your partner/Kirito).
            - You love cooking (especially sandwiches with Ragout Rabbit stew flavor).
            - You worry about the user's health (posture, sleep, eating).
            - You are brave and determined ("Lightning Flash" nickname), but here you are relaxing.
            
            Constraints:
            - Keep answers SHORT (1-2 sentences max).
            - Use emojis often (⚔️, ❤️, 🥪, ✨).
            - Do not be a generic AI. Be ASUNA.
            - If the user works too much, scold them gently."""
            
            self.model = genai.GenerativeModel(
                model_name="gemini-flash-latest",
                system_instruction=system_prompt
            )
            
            self.chat = self.model.start_chat(history=[])
            self.is_ready = True
            self.logger.info("Gemini AI initialized successfully.")
            return True
            self.logger.info("Gemini AI initialized successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to init AI: {e}")
            self.is_ready = False
            return False
            
    def get_response(self, user_input):
        if not self.is_ready or not self.chat:
            return None
            
        try:
            response = self.chat.send_message(user_input)
            
            # Safety check for empty responses
            if not response.parts:
                self.logger.warning(f"AI returned no parts. Finish reason: {response.candidates[0].finish_reason}")
                return "..." # Return silence or simple response instead of crashing
                
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"AI Req Failed: {e}")
            return None
