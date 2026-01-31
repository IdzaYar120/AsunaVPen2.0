import json, os, logging
from config.settings import Settings

class StatsManager:
    def __init__(self):
        self.data = self.load_stats()

    def load_stats(self):
        default = {
            "hunger": 100.0, "energy": 100.0, "health": 100.0, "happiness": 100.0,
            "xp": 0, "level": 1, "money": 50, "inventory": {"sandwich": 2, "ball": 1},
            "achievements": [],
            "tasks": []
        }
        
        # Try loading mostly recent
        data = self._load_file(Settings.SAVE_PATH)
        if data: return self._validate(data)
        
        # Try backup
        backup_path = Settings.SAVE_PATH + ".bak"
        if os.path.exists(backup_path):
            logging.warning("Main save corrupt/missing, loading backup.")
            data = self._load_file(backup_path)
            if data: return self._validate(data)
            
        return default

    def _load_file(self, path):
        if not os.path.exists(path): return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load stats from {path}: {e}")
            return None

    def _validate(self, data):
        # Ensure all keys exist (migration)
        defaults = {
            "happiness": 100.0, "money": 50, "tasks": [],
            "daily_tasks_completed": 0, "last_task_date": "",
            "achievements": [], "games_played": 0,
            "minutes_worked": 0, "gemini_api_key": ""
        }
        for k, v in defaults.items():
            if k not in data: data[k] = v
        return data

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

        # 4. Health Logic
        h_decay = 0.0
        # If starving or exhausted
        if self.data["hunger"] < 20 or self.data["energy"] < 10:
             h_decay = 0.05
        
        if self.data["hunger"] <= 1:
             h_decay = 0.2 # Starvation

        if h_decay > 0:
            self.data["health"] = max(0.0, min(max_val, self.data["health"] - h_decay))

    def heal(self, amount):
        max_val = self.get_max_stats()
        self.data["health"] = min(max_val, self.data["health"] + amount)

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

    def add_item(self, i_id, count=1):
        """Safely add item to inventory."""
        self.data["inventory"][i_id] = self.data["inventory"].get(i_id, 0) + count

    def unlock_achievement(self, a_id):
        if a_id in Settings.ACHIEVEMENTS and a_id not in self.data["achievements"]:
            self.data["achievements"].append(a_id)
            return True
        return False

    def save_stats(self):
        try:
            os.makedirs(os.path.dirname(Settings.SAVE_PATH), exist_ok=True)
            tmp_path = Settings.SAVE_PATH + ".tmp"
            bak_path = Settings.SAVE_PATH + ".bak"
            
            # Atomic Write: Write to tmp first
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
                
            # If successful, backup old save and rename new one
            if os.path.exists(Settings.SAVE_PATH):
                try:
                    os.replace(Settings.SAVE_PATH, bak_path)
                except OSError:
                    pass # Backup failed, but we still want to save new data
            
            os.replace(tmp_path, Settings.SAVE_PATH)
            
        except Exception as e:
            logging.error(f"Failed save_stats: {e}")