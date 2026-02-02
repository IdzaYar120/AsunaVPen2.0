import logging
from config.settings import Settings

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class AIClient:
    def __init__(self):
        self.client = None
        self.chat = None
        self.is_ready = False
        self.logger = logging.getLogger("AIClient")

    def init_ai(self, api_key):
        if not HAS_GENAI:
            self.logger.error("Library 'google-genai' missing. Run: pip install google-genai")
            return False

        if not api_key:
            self.logger.warning("API Key missing.")
            return False
            
        try:
            self.client = genai.Client(api_key=api_key)
            
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
            
            # Start Chat Session
            self.chat = self.client.chats.create(
                model="gemini-2.0-flash",
                config={"system_instruction": system_prompt},
                history=[]
            )
            
            self.is_ready = True
            self.logger.info("Gemini AI initialized successfully (New SDK).")
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
            
            if not response or not response.text:
                return "..."
                
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"AI Req Failed: {e}")
            return None
