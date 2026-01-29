import json, os, logging
from config.settings import Settings

class StatsManager:
    def __init__(self):
        self.data = self.load_stats()

    def load_stats(self):
        default = {
            "hunger": 100.0, "energy": 100.0, "health": 100.0, "happiness": 100.0,
            "xp": 0, "level": 1, "money": 50, "inventory": {"sandwich": 2, "ball": 1},
            "tasks": []
        }
        if not os.path.exists(Settings.SAVE_PATH): return default
        try:
            with open(Settings.SAVE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "happiness" not in data: data["happiness"] = 100.0
                if "money" not in data: data["money"] = 50
                if "tasks" not in data: data["tasks"] = []
                if "daily_tasks_completed" not in data: data["daily_tasks_completed"] = 0
                if "last_task_date" not in data: data["last_task_date"] = ""
                if "achievements" not in data: data["achievements"] = []
                if "games_played" not in data: data["games_played"] = 0
                if "minutes_worked" not in data: data["minutes_worked"] = 0
                return data
        except: return default

    def get_max_stats(self):
        # 100 + (Lvl-1)*20
        # Lvl 1: 100
        # Lvl 2: 120
        # Lvl 3: 140
        return 100.0 + (self.data["level"] - 1) * Settings.STAT_BOOST_PER_LEVEL

    def get_next_level_xp(self):
        # Base * Level
        # Lvl 1 -> 2: 100
        # Lvl 2 -> 3: 200
        # Lvl 3 -> 4: 300
        return Settings.BASE_XP_REQ * self.data["level"]

    def update(self, current_state, is_neglected=False):
        base = Settings.STATS_DECAY_BASE
        max_val = self.get_max_stats()
        
        # 1. Hunger
        h_m = 1.2 if current_state == "working" else 1.0
        self.data["hunger"] = max(0.0, min(max_val, self.data["hunger"] - base * h_m))

        # 2. Happiness
        if current_state == "training": h_d = Settings.HAPPINESS_DECAY_TRAIN
        elif current_state == "working": h_d = Settings.HAPPINESS_DECAY_WORK
        elif current_state in ["angry", "drag"]: h_d = Settings.HAPPINESS_DECAY_ANGRY
        else: h_d = Settings.HAPPINESS_DECAY_IDLE
        
        if self.data["hunger"] < 25 or self.data["energy"] < 25: h_d *= 2.0
        if is_neglected: h_d += Settings.HAPPINESS_DECAY_NEGLECT
        self.data["happiness"] = max(0.0, min(100.0, self.data["happiness"] - h_d)) # Max 100 for happiness

        # 3. Energy
        if current_state == "idle": e_m = Settings.ENERGY_DECAY_IDLE
        elif current_state == "walk": e_m = Settings.ENERGY_DECAY_WALK
        elif current_state == "working": e_m = Settings.ENERGY_DECAY_WORK
        else: e_m = 1.0
        if current_state != "sleep":
            self.data["energy"] = max(0.0, min(max_val, self.data["energy"] - (base * e_m)))

    def add_xp(self, amount):
        self.data["xp"] += amount
        leveled = False
        req = self.get_next_level_xp()
        while self.data["xp"] >= req:
            self.data["xp"] -= req
            self.data["level"] += 1
            leveled = True
            # Recalculate requirement for next loop if multiple levels gained
            req = self.get_next_level_xp()
        return leveled
        
    def use_item(self, i_id):
        if self.data["inventory"].get(i_id, 0) > 0:
            self.data["inventory"][i_id] -= 1; return True
        return False

    def unlock_achievement(self, a_id):
        if a_id in Settings.ACHIEVEMENTS and a_id not in self.data["achievements"]:
            self.data["achievements"].append(a_id)
            return True
        return False

    def save_stats(self):
        try:
            os.makedirs(os.path.dirname(Settings.SAVE_PATH), exist_ok=True)
            tmp = Settings.SAVE_PATH + ".tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            os.replace(tmp, Settings.SAVE_PATH)
        except: pass