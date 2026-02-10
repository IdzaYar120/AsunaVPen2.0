import random
import time
from config.settings import Settings

class MailManager:
    """Handles receiving letters and gifts from SAO characters."""
    CHARACTERS = {
        "kirito": {"name": "Кіріто", "avatar": "kirito.png", "relation": "Коханий"},
        "yui": {"name": "Юі", "avatar": "yui.png", "relation": "Донечка"},
        "silica": {"name": "Сіліка", "avatar": "silica.png", "relation": "Подруга"},
        "lisbeth": {"name": "Лізбет", "avatar": "lisbeth.png", "relation": "Подруга"},
        "klein": {"name": "Кляйн", "avatar": "klein.png", "relation": "Друг"}
    }

    LETTERS = [
        "Привіт! Знайшов це під час рейду і подумав про тебе. Сподіваюся, пригодиться! ⚔️",
        "Мамо, дивись що я знайшла! Це для тебе і Тата! Люблю вас! ❤️",
        "Привіт, Асуно! Спекла сьогодні нове печиво, спробуй обов'язково! ✨",
        "Гей! Маю зайвий предмет, бери собі. Удачі вам там! 🔥",
        "Асуно, привіт! Бачила це в магазині і відразу згадала про тебе. Сподіваюся, тобі сподобається! 🎁"
    ]

    GIFTS = ["panna_cotta", "sandwich", "chocolate", "apple", "gem", "flowers", "teddy-bear"]

    def __init__(self, stats):
        self.stats = stats
        self.last_check = time.time()

    def check_for_mail(self):
        """Randomly returns a new mail object if successful."""
        # Check every 30 minutes in reality, but for testing we can lower it.
        if time.time() - self.last_check < 1800: 
            return None
        
        self.last_check = time.time()
        
        if random.random() < 0.1: # 10% chance every check
            char_id = random.choice(list(self.CHARACTERS.keys()))
            return {
                "sender_id": char_id,
                "sender_name": self.CHARACTERS[char_id]["name"],
                "text": random.choice(self.LETTERS),
                "gift_item": random.choice(self.GIFTS),
                "timestamp": time.time()
            }
        return None
