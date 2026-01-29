import json, os, logging
from config.settings import Settings

class StatsManager:
    def __init__(self):
        self.data = self.load_stats()

    def load_stats(self):
        default = {
            "hunger": 100.0, "energy": 100.0, "health": 100.0, "happiness": 100.0,
            "xp": 0, "level": 1, "money": 50, "inventory": {"sandwich": 2, "ball": 1}
        }
        if not os.path.exists(Settings.SAVE_PATH): return default
        try:
            with open(Settings.SAVE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "happiness" not in data: data["happiness"] = 100.0
                if "money" not in data: data["money"] = 50
                return data
        except: return default

    def update(self, current_state, is_neglected=False):
        base = Settings.STATS_DECAY_BASE
        # 1. Голод
        h_m = 1.2 if current_state == "working" else 1.0
        self.data["hunger"] = max(0.0, self.data["hunger"] - base * h_m)

        # 2. Щастя
        if current_state == "training": h_d = Settings.HAPPINESS_DECAY_TRAIN
        elif current_state == "working": h_d = Settings.HAPPINESS_DECAY_WORK
        elif current_state in ["angry", "drag"]: h_d = Settings.HAPPINESS_DECAY_ANGRY
        else: h_d = Settings.HAPPINESS_DECAY_IDLE
        
        if self.data["hunger"] < 25 or self.data["energy"] < 25: h_d *= 2.0
        if is_neglected: h_d += Settings.HAPPINESS_DECAY_NEGLECT
        self.data["happiness"] = max(0.0, self.data["happiness"] - h_d)

        # 3. Енергія
        if current_state == "idle": e_m = Settings.ENERGY_DECAY_IDLE
        elif current_state == "walk": e_m = Settings.ENERGY_DECAY_WALK
        elif current_state == "working": e_m = Settings.ENERGY_DECAY_WORK
        else: e_m = 1.0
        if current_state != "sleep":
            self.data["energy"] = max(0.0, self.data["energy"] - (base * e_m))

    def add_xp(self, amount):
        self.data["xp"] += amount
        leveled = False
        while self.data["xp"] >= Settings.LEVEL_UP_XP:
            self.data["xp"] -= Settings.LEVEL_UP_XP; self.data["level"] += 1; leveled = True
        return leveled

    def use_item(self, i_id):
        if self.data["inventory"].get(i_id, 0) > 0:
            self.data["inventory"][i_id] -= 1; return True
        return False

    def save_stats(self):
        try:
            os.makedirs(os.path.dirname(Settings.SAVE_PATH), exist_ok=True)
            tmp = Settings.SAVE_PATH + ".tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            os.replace(tmp, Settings.SAVE_PATH)
        except: pass