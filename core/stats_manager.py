import json
import os
import logging
from config.settings import Settings

logger = logging.getLogger(__name__)

class StatsManager:
    def __init__(self):
        self.data = self.load_stats()

    def load_stats(self):
        default = {
            "hunger": 100.0, "energy": 100.0, "health": 100.0,
            "xp": 0, "level": 1, "inventory": {"sandwich": 3, "lollipop": 5}
        }
        if not os.path.exists(Settings.SAVE_PATH): return default
        try:
            with open(Settings.SAVE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for k, v in default.items():
                    if k not in data: data[k] = v
                return data
        except Exception as e:
            logger.error(f"Load error: {e}")
            return default

    def add_xp(self, amount):
        self.data["xp"] += amount
        leveled = False
        while self.data["xp"] >= Settings.LEVEL_UP_XP:
            self.data["xp"] -= Settings.LEVEL_UP_XP
            self.data["level"] += 1
            leveled = True
        return leveled

    def update(self):
        decay = Settings.STATS_DECAY_RATE
        self.data["hunger"] = max(0.0, self.data["hunger"] - decay)
        self.data["energy"] = max(0.0, self.data["energy"] - decay * 0.7)
        if self.data["hunger"] < 15: self.data["health"] = max(0.0, self.data["health"] - decay)

    def use_item(self, i_id):
        if self.data["inventory"].get(i_id, 0) > 0:
            self.data["inventory"][i_id] -= 1
            return True
        return False

    def save_stats(self):
        try:
            os.makedirs(os.path.dirname(Settings.SAVE_PATH), exist_ok=True)
            tmp = Settings.SAVE_PATH + ".tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            os.replace(tmp, Settings.SAVE_PATH)
        except Exception as e:
            logger.error(f"Save error: {e}")