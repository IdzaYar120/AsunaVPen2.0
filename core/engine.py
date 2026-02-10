import random
import time
import logging
import os
import sys
import winreg
from datetime import datetime

# 3rd Party
from PyQt6.QtCore import QTimer, QObject, QCoreApplication
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtMultimedia import QMediaPlayer

# Core
from core.resource_manager import ResourceManager
from core.stats_manager import StatsManager
from core.task_manager import TaskManager
from core.cooking_manager import CookingManager
from core.garden_manager import GardenManager
from core.sound_manager import SoundManager
from core.dialogues import QUOTES, WINDOW_KEYWORDS, WINDOW_REACTIONS
from core import window_reader
from core.ai_client import AIClient
from core.music_player import MusicPlayer
from core.system_monitor import SystemMonitor
from core.journal_manager import JournalManager
from core.mail_manager import MailManager

# UI
from core.window_manager import WindowManager
from core.interaction_handler import InteractionHandler

# Config
from config.settings import Settings

logger = logging.getLogger(__name__)

class PetEngine(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.res = ResourceManager()
        self.res.load_essential()
        
        self.stats = StatsManager()
        self.task_manager = TaskManager(self.stats)
        self.cooking_manager = CookingManager(self.stats)
        self.garden_manager = GardenManager(self.stats)
        self.sound = SoundManager()
        
        self.load_language() # Load Strings
        
        self.ai = AIClient()
        if self.stats.data.get("gemini_api_key"):
            try:
                self.ai.init_ai(self.stats.data["gemini_api_key"])
            except Exception as e:
                logger.error(f"Failed to init AI on startup: {e}")
            
        self.music_player = MusicPlayer()
        
        # System Monitor (Background)
        self.sys_monitor = SystemMonitor()
        
        # Social Features
        self.journal = JournalManager(self.stats.DATA_DIR)
        self.mail_manager = MailManager(self.stats)

        # States and Animation
        self.current_state = "idle"
        self.direction = 1
        self.frame_index = 0
        
        self.last_anim_time = time.time() * 1000
        self.is_emotion_locked = False
        
        self.window_manager = WindowManager(self)
        
        self.last_window_title = ""
        self.last_window_check = 0
        self.last_window_reaction_time = 0
        self.last_game_time = 0
        self.last_mail_check = time.time()
        
        self.interaction = InteractionHandler(self)
        
        # Interaction State
        self.click_count, self.last_click_time, self.drag_start_time = 0, 0, 0
        self.tired_remind_counter = 0
        self.last_interaction_time = time.time()

        # Pomodoro Timer
        self.work_timer = QTimer(self); self.work_timer.timeout.connect(self.tick_work)
        self.work_seconds_left = 0
        self.current_session_mins = 0

        # Save on Exit
        QCoreApplication.instance().aboutToQuit.connect(self.stats.save_stats)

        # Main Loops
        self.update_timer = QTimer(self); self.update_timer.timeout.connect(self.update_loop)
        self.update_timer.start(1000 // Settings.TARGET_FPS)
        
        self.ai_timer = QTimer(self); self.ai_timer.timeout.connect(self.think)
        self.ai_timer.start(Settings.AI_THINK_INTERVAL)

    def load_language(self):
        try:
            import json, os
            path = os.path.join("assets", "lang", "uk.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self.lang = json.load(f)
            else:
                self.lang = {}
        except Exception as e:
            logger.error(f"Failed to load language: {e}")
            self.lang = {}

    def _t(self, key, **kwargs):
        keys = key.split(".")
        val = self.lang
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, key)
            else:
                val = key
                break
        
        if val == key and "." in key:
            # Fallback if key not found but has dots (return key itself usually)
            return key
            
        if isinstance(val, list): return random.choice(val)
        if isinstance(val, str): return val.format(**kwargs)
        return str(val)

    def update_loop(self):
        # Update UI with support for dynamic MAX stats
        max_val = self.stats.get_max_stats()
        self.window.update_stats_ui(
            self.stats.data["hunger"], self.stats.data["energy"], 
            self.stats.data["health"], self.stats.data["happiness"],
            max_val
        )
        self.window.update_xp_ui(self.stats.data["xp"], self.stats.data["level"], self.stats.get_next_level_xp())
        
        # Needs calculation considering neglect
        neglected = (time.time() - self.last_interaction_time) > Settings.NEGLECT_THRESHOLD
        self.stats.update(self.current_state, neglected)
        

            
        # Active Window Check (every 5s)
        if time.time() - self.last_window_check > 5:
            self.check_active_window()
            self.last_window_check = time.time()
            
            # Random Event: Guessing Game (Check cooldown + chance)
            # Ensure at least 10 minutes between games to prevent spam
            if (time.time() - self.last_game_time > 600) and self.current_state == "idle":
                if random.random() < 0.05: # 5% chance every 5s if cooldown passed
                    self.start_guessing_game()
                    self.last_game_time = time.time()
            
            # Check for Mail (every 10 minutes)
            if time.time() - self.last_mail_check > 600:
                self.last_mail_check = time.time()
                mail = self.mail_manager.check_for_mail()
                if mail:
                    self.window_manager.show_mail(mail)

        # State Priorities
        if self.window.is_dragging:
            self.handle_dragging()
        elif self.current_state == "walk" and not self.is_emotion_locked:
            self.move_pet()
        elif self.stats.data["happiness"] < Settings.HAPPINESS_THRESHOLD_SAD and not self.is_emotion_locked:
            if self.current_state not in ["sleep", "working", "training"]:
                self.set_state("sad")

        # Animation Update
        now = time.time() * 1000
        if now - self.last_anim_time > Settings.ANIMATION_SPEED:
            self.update_animation(); self.last_anim_time = now
            
        # Sync Music Widget
        self.window_manager.update_music_widget_pos()
            
        self.handle_energy_logic()

    def trigger_emotion(self, state, duration):
        # Special Logic for Dance (Music Reaction) - Support for Sing/Dance + Rewards
        if state == "dance":
             options = []
             if os.path.exists(os.path.join(Settings.ANIM_DIR, "dance")): options.append("dance")
             if os.path.exists(os.path.join(Settings.ANIM_DIR, "sing")): options.append("sing")
             
             if options:
                 state = random.choice(options)
                 self.res.load_animation(state) # Lazy Load
                 # Rewards & Visuals
                 reward = Settings.DANCE_XP_REWARD
                 self.stats.add_xp(reward)
                 self.window.create_floating_text(f"+{reward} XP", "#00FF00")
                 particle = "✨" if state == "dance" else "🎵"
                 p_color = "#FFD700" if state == "dance" else "#00BFFF"
                 self.window.spawn_particles(particle, 8, p_color)
                 
        if self.is_emotion_locked: return
        
        # Lazy Load Emotion
        self.res.load_animation(state)
        
        self.set_state(state)
        self.is_emotion_locked = True
        QTimer.singleShot(duration, self.release_emotion)

    def release_emotion(self):
        """Return to normal state after emotion ends."""
        # if self.window.is_dragging: return # REMOVED: Caused stuck lock if dragging during timeout
        
        # Return Priority: Work -> Sad -> Tired -> Idle
        if self.work_timer.isActive():
            self.set_state("working")
            return
            
        # Unload heavy animations if they were active
        if self.current_state in ["training", "dance", "sing", "excited", "playing", "eat"]:
            self.res.unload_animation(self.current_state)

        if self.stats.data["happiness"] < Settings.HAPPINESS_THRESHOLD_SAD:
            self.set_state("sad")
        elif self.stats.data["energy"] < Settings.ENERGY_THRESHOLD_TIRED:
            self.set_state("tired")
        else:
            self.is_emotion_locked = False
            self.set_state("idle")

    def check_happiness_block(self):
        """Block actions if Asuna is unhappy."""
        if self.stats.data["happiness"] < Settings.HAPPINESS_THRESHOLD_SAD:
            self.window.show_emote("angry")
            self.window.show_emote("angry")
            self.sound.play("angry")
            self.window.create_floating_text(self._t("emote_sad"), "#FF4444")
            return True
        return False

    def train(self):
        if self.current_state in ["sleep", "tired", "working"] or self.is_emotion_locked: return
        if self.check_happiness_block(): return # Mood Check
        
        if self.stats.data["energy"] < 25:
            self.window.show_emote("tired"); return
        
        self.res.load_animation("training")
        self.trigger_emotion("training", 4000)
        self.sound.play_looped("training", 4000)
        self.stats.data["energy"] -= 25
        self.stats.data["money"] += Settings.COINS_PER_TRAINING
        
        xp = Settings.XP_PER_TRAINING
        coins = Settings.COINS_PER_TRAINING
        QTimer.singleShot(1000, lambda: self.window.create_floating_text(f"+{xp} XP", "#FFD700"))
        QTimer.singleShot(2000, lambda: self.window.create_floating_text(f"+{coins} 💰", "#FFCC00"))
        if self.stats.add_xp(xp): 
            QTimer.singleShot(4100, self.trigger_levelup)
            
        self.check_quests("train", "any", delay_victory=4000)
        self.journal.log_event("train")

    def check_quests(self, event_type, value, delay_victory=0):
        rewards = self.task_manager.check_event(event_type, value)
        for r in rewards:
            # Apply rewards immediately
            self.stats.data["money"] += r["money"]
            self.stats.add_xp(r["xp"])
            hap = r.get("happiness", 10)
            self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + hap)
            
            # Delayed animation and text
            # Delayed animation and text
            QTimer.singleShot(delay_victory, lambda: self.window.create_floating_text(self._t("quest_completed"), "#00FF00"))
            QTimer.singleShot(delay_victory + 500, lambda r=r: self.window.create_floating_text(f"+{r['money']} 💰  +{r['xp']} XP", "#FFD700"))
            QTimer.singleShot(delay_victory + 1500, lambda h=hap: self.window.create_floating_text(f"+{h} ❤️", "#FF69B4"))
            
            if r.get("bonus_applied"):
                 QTimer.singleShot(delay_victory + 2000, lambda: self.window.create_floating_text("🎁 DAILY BONUS! 🎁", "#FF00FF"))

            QTimer.singleShot(delay_victory, lambda: self.trigger_emotion("excited", 4000))
            QTimer.singleShot(delay_victory, lambda: self.sound.play("happy"))
        
        # Always update list to reflect progress
        # Always update list to reflect progress
        # Always update list to reflect progress
        if self.window_manager.todo_win and not self.window_manager.todo_win.isHidden():
            self.window_manager.todo_win.refresh_list()


    def trigger_levelup(self):
        # Level Up Reward
        reward = Settings.LEVEL_UP_REWARD_COINS
        self.stats.data["money"] += reward
        
        self.trigger_emotion("excited", 4000)
        self.window.create_floating_text(f"LEVEL UP! {self.stats.data['level']}", "#00FF00")
        QTimer.singleShot(1500, lambda: self.window.create_floating_text(f"+{reward} 💰", "#FFD700"))
        
        self.window.show_emote("happy")
        self.sound.play("happy")

        # Power up! Refill stats to new max
        max_v = self.stats.get_max_stats()
        self.stats.data["hunger"] = max_v
        self.stats.data["energy"] = max_v
        self.stats.data["health"] = max_v
        self.update_loop() # Refresh UI immediately

    def start_work_session(self, mins):
        if self.current_state in ["sleep", "tired"] or self.is_emotion_locked: return
        if self.check_happiness_block(): return # Перевірка настрою
        
        self.current_session_mins = mins
        self.work_seconds_left = mins * 60
        self.is_emotion_locked = True
        self.set_state("working")
        self.work_timer.start(1000)
        self.window.show_emote("happy")

    def use_item_from_inventory(self, i_id):
        # Allow items to break the lock (e.g. food soothes anger)
        self.is_emotion_locked = False 
        self.reset_interaction()
        
        if i_id in Settings.GIFT_STATS:
            if self.stats.use_item(i_id):
                gain = Settings.GIFT_STATS[i_id]
                self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + gain)
                self.trigger_emotion("excited", 4000); self.window.show_emote("happy"); self.sound.play("arigato")
                self.window.create_floating_text(f"+{gain} ❤️", "#FF69B4")
                self.check_quests("eat", i_id, delay_victory=4000) # Gift treated as eat/use
        elif i_id == "medicine":
            if self.stats.use_item(i_id):
                self.stats.heal(Settings.MEDICINE_HEAL_AMOUNT)
                self.trigger_emotion("eat", 2000) 
                self.talk_text(self._t("system.emote_thanks"))
                self.window.create_floating_text(f"+{Settings.MEDICINE_HEAL_AMOUNT} Health ❤️", "#FF4444")
        elif i_id in Settings.PLAY_ITEMS:
            if self.current_state == "sleep": return
            if self.stats.use_item(i_id):
                self.stats.data["energy"] = max(0, self.stats.data["energy"] - 15)
                self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 30)
                self.trigger_emotion("playing", 5000)
                self.window.create_floating_text("+30 ❤️", "#FF69B4")
                if self.stats.add_xp(Settings.PLAY_XP_REWARD): self.trigger_levelup()
                
        # Garden Items - Safe Guard
        elif i_id == "watering_can" or i_id.startswith("seed_"):
             self.window.create_floating_text(self._t("system.use_in_garden"), "#FFD700")
             return
             
        else: # Food / Sweets / Healthy
            if i_id in Settings.PREPARED_FOODS:
                self.stats.data["eaten_cooked"] = self.stats.data.get("eaten_cooked", 0) + 1
            
            is_sweet = i_id in Settings.SWEET_STATS
            is_healthy = i_id in Settings.HEALTH_FOOD_STATS
            
            t_stat = "energy" if is_sweet else "hunger"
            max_val = self.stats.get_max_stats()
            
            # Check if full (only for pure food/sweets, healthy items might be used for health)
            if not is_healthy and self.stats.data[t_stat] >= max_val - 5: 
                self.trigger_emotion("angry", 3000); self.window.show_emote("angry"); self.sound.play("angry"); return
                
            if self.stats.use_item(i_id):
                if is_healthy:
                    # Healthy Food Logic (Hunger, Health)
                    h_gain, hp_gain = Settings.HEALTH_FOOD_STATS[i_id]
                    self.stats.data["hunger"] = min(max_val, self.stats.data["hunger"] + h_gain)
                    self.stats.heal(hp_gain)
                    self.window.create_floating_text(f"+{h_gain} 🍗 +{hp_gain} ❤️", "#90EE90")
                    self.trigger_emotion("eat", 3000)
                else:
                    # Standard Food/Sweets
                    gain = Settings.SWEET_STATS[i_id] if is_sweet else Settings.FOOD_STATS[i_id]
                    self.stats.data[t_stat] = min(max_val, self.stats.data[t_stat] + gain)
                    
                    # Sweets add a little happiness
                    if is_sweet:
                        self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 5)
                        self.window.create_floating_text("+5 ❤️", "#FF69B4")
                    
                    self.trigger_emotion("eat", 5000)
                
                if is_sweet or self.current_state in ["sleep", "tired"]: self.is_emotion_locked = False
                self.window.show_emote("happy")
                self.sound.play_looped("eat", 3000)
                self.check_quests("eat", i_id, delay_victory=3000)
        
        if self.window_manager.inventory_win: self.window_manager.inventory_win.refresh()

    def handle_energy_logic(self):
        e = self.stats.data["energy"]
        max_val = self.stats.get_max_stats()
        
        if self.window.is_dragging: return
        if self.current_state == "sleep":
            self.stats.data["energy"] = min(max_val, e + 0.1)
            if self.stats.data["energy"] >= max_val: self.wake_up()
        elif self.current_state not in ["working", "training"]:
            if e < Settings.ENERGY_THRESHOLD_SLEEP: self.toggle_sleep()
            elif e < Settings.ENERGY_THRESHOLD_TIRED:
                if self.current_state != "tired" and not self.is_emotion_locked:
                    self.set_state("tired"); self.window.show_emote("tired")

    def reset_interaction(self):
        self.last_interaction_time = time.time()
        if self.current_state == "sad" and self.stats.data["happiness"] >= Settings.HAPPINESS_THRESHOLD_SAD:
            self.is_emotion_locked = False; self.set_state("idle")

    def think(self):
        # 1. Priority: Cooking Mode (Persistent)
        if self.window_manager.cooking_win and self.window_manager.cooking_win.isVisible():
            if not self.is_emotion_locked and self.current_state != "cooking":
                self.set_state("cooking")
                self.window.show_emote("cooking")
            if not self.is_emotion_locked: return # Prevent other idle behaviors if we are cooking

        if self.window.is_dragging or self.is_emotion_locked or self.current_state in ["sleep", "tired", "working", "sad"]: return
        
        # Chance to Dance if Music is Playing
        # Chance to Dance/Sing if Music is Playing
        if self.music_player and self.music_player.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
             if random.random() < 0.4: # 40% chance every 5s
                 self.trigger_emotion("dance", 5000) # Logic handled in trigger_emotion
             if random.random() < 0.05:
                self.check_system_reactions()

        # 3. Random Idle Behavior
        if random.random() < 0.3:
            self.set_state("walk"); self.direction = random.choice([1, -1])
        else: self.set_state("idle")
        
        # Chance for random idle talk (1% per think interval)
        if random.random() < 0.05:
            self.talk(auto=True)

        # Health Consequences
        if self.stats.data["health"] < 30:
             if random.random() < 0.1: # 10% chance
                 self.trigger_emotion("tired", 3000)
                 self.talk_text(random.choice([self._t("system.ill_nausea"), self._t("system.ill_pills")]))

    def check_system_reactions(self):
        if not hasattr(self, 'sys_monitor'): return
        
        stats = self.sys_monitor.get_stats()
        
        # High CPU Reaction
        if stats["cpu"] > 80:
            self.trigger_emotion("tired", 4000)
            self.talk_text(self._t("system.sys_cpu"))
            return

        # Low Battery Reaction
        if stats["battery"] is not None and stats["battery"] < 20 and not stats["plugged"]:
            self.trigger_emotion("scared", 4000)
            self.talk_text(self._t("system.sys_battery"))
            return
            
        # High RAM Reaction
        if stats["ram_percent"] > 90:
             self.trigger_emotion("confused", 4000)
             self.talk_text(self._t("system.sys_ram"))
        
        # Chance for new quest (5% every 5s approx)
        if random.random() < 0.05:
            if self.task_manager.generate_random_quest():
                self.window.show_emote("quest")
                self.sound.play("quest")
                self.sound.play("quest")
                if self.window_manager.todo_win and not self.window_manager.todo_win.isHidden(): 
                    self.window_manager.todo_win.refresh_list()
        
        # Chance for random idle talk (1% per think interval)
        if random.random() < 0.05:
            self.talk(auto=True)

    def move_pet(self):
        screen = QApplication.primaryScreen().availableGeometry()
        nx = self.window.x() + (self.direction * Settings.WALK_SPEED)
        if nx < 10 or nx > screen.width() - self.window.width() - 10: self.direction *= -1; self.set_state("idle")
        else: self.window.move(int(nx), self.window.y())

    def update_animation(self):
        key = self.current_state
        if key == "walk": key = "walk_right" if self.direction == 1 else "walk_left"
        frames = self.res.get_frames(key)
        if frames:
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.window.render_pet(frames[self.frame_index])

    def open_achievements(self):
        self.window_manager.open_achievements()

    def on_achievement_unlocked(self, name, icon):
        self.window.show_achievement_popup(name, icon)
        self.sound.play("happy")
        self.journal.log_event("achievement", details=name)

    def wake_up(self): 
        self.is_emotion_locked = False; self.set_state("idle")
        self.sound.stop("sleep")
    def handle_drag_start(self): 
        self.interaction.handle_drag_start()
    def handle_dragging(self):
        self.interaction.handle_dragging()
    def toggle_sleep(self):
        if self.current_state == "sleep": self.wake_up()
        else: 
            self.set_state("sleep"); self.is_emotion_locked = True; self.window.show_emote("sleepy")
            self.sound.start_loop("sleep")
    def tick_work(self):
        if self.work_seconds_left > 0:
            self.work_seconds_left -= 1; m, s = divmod(self.work_seconds_left, 60); self.window.update_timer_display(f"{m:02d}:{s:02d}")
        else: self.complete_work_session()
    def complete_work_session(self):
        self.work_timer.stop(); self.window.update_timer_display(None)
        xp, money = self.current_session_mins * Settings.WORK_XP_MULTIPLIER, self.current_session_mins * Settings.WORK_COIN_MULTIPLIER
        self.stats.data["money"] += money; self.window.create_floating_text(f"+{xp} XP", "#FFD700")
        QTimer.singleShot(1000, lambda: self.window.create_floating_text(f"+{money} 💰", "#FFCC00"))
        if self.stats.add_xp(xp): QTimer.singleShot(2500, self.trigger_levelup)
        self.check_quests("work", self.current_session_mins)
        self.journal.log_event("work", details=f"{self.current_session_mins} хв")
        self.is_emotion_locked = False; self.set_state("idle")
    def stop_work_session(self):
        self.work_timer.stop(); self.window.update_timer_display(None)
        self.is_emotion_locked = False; self.set_state("idle"); self.window.show_emote("angry"); self.sound.play("angry")
    def buy_item(self, i_id, price):
        if self.stats.data["money"] >= price:
            self.stats.data["money"] -= price
            
            # Logic for recipes
            if i_id.startswith("recipe_"):
                self.cooking_manager.unlock_recipe(i_id)
                if self.window_manager.cooking_win:
                    # Trigger refresh if window exists
                    self.window_manager.cooking_win.refresh_recipes()
            else:
                inv = self.stats.data["inventory"]
                inv[i_id] = inv.get(i_id, 0) + 1
            
            self.window.create_floating_text(f"-{price} 💰", "#FF5555")
            self.window.show_emote("happy")
            self.trigger_emotion("excited", 3000) # React to purchase
            self.check_quests("buy", i_id)
            self.stats.save_stats()
            
            if self.window_manager.shop_win: self.window_manager.shop_win.refresh_shop()
            if self.window_manager.inventory_win: self.window_manager.inventory_win.refresh()
            return True
        else:
            self.window.show_emote("angry")
            self.window.create_floating_text(self._t("system.shop_no_money"), "#FF0000")
            self.sound.play("angry")
            return False
    def open_inventory(self):
        self.window_manager.open_inventory()

    def open_shop(self):
        self.window_manager.open_shop()

    def open_garden(self):
        self.window_manager.open_garden()
        
    def open_cooking(self):
        self.window_manager.open_cooking()

    def close_cooking(self):
        self.window_manager.close_cooking()

    def open_todo_list(self):
        self.window_manager.open_todo_list()

    def open_music_player(self):
        self.window_manager.open_music_player()
    
    def dock_music_player(self):
        self.window_manager.dock_music_player()

    def close_all_windows(self):
        self.window_manager.close_all()
        
    def open_settings(self):
        self.window_manager.open_settings()

    def open_journal(self):
        self.window_manager.open_journal()
        
    def open_minigame(self):
        self.window_manager.open_minigame()

    def open_slots(self):
        self.window_manager.open_slots()

    def start_dancing(self):
        if self.current_state in ["sleep", "tired", "working"]: return
        if self.current_state in ["dance", "sing"]: return # Prevent spamming
        if not self.is_emotion_locked:
            options = ["dance"]
            # Check if 'sing' folder exists, load it if chosen
            if os.path.exists(os.path.join(Settings.ANIM_DIR, "sing")): options.append("sing")
            
            chosen = random.choice(options)
            
            # Lazy Load
            self.res.load_animation(chosen)
            
            self.set_state(chosen)
            self.window.spawn_particles("🎵" if chosen == "sing" else "✨", 8, Settings.COLORS["particle_sing" if chosen == "sing" else "particle_dance"])
            
            # Auto release after 5 seconds
            QTimer.singleShot(5000, self.release_emotion)

    def use_item_from_inventory(self, i_id):
        if self.stats.use_item(i_id):
            # 1. Play Items (Ball, Joystick)
            if i_id in Settings.PLAY_ITEMS:
                if not self.is_emotion_locked:
                    self.res.load_animation("playing")
                    self.set_state("playing")
                    self.window.spawn_particles("🎾" if i_id == "ball" else "🎮", 8, "#FFFFFF")
                    self.sound.play("happy")
                    self.journal.log_event("play", details=i_id)
                    
                    # Add stats
                    self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 15)
                    self.stats.add_xp(Settings.PLAY_XP_REWARD)
                    
                    self.window.create_floating_text(f"+{Settings.PLAY_XP_REWARD} XP", Settings.COLORS["particle_xp"])
                    
                    QTimer.singleShot(4000, self.release_emotion)
                    
            # 2. Food
            elif i_id in Settings.FOOD_STATS or i_id in Settings.SWEET_STATS or i_id in Settings.HEALTH_FOOD_STATS:
                self.feed(i_id)
                
            # 3. Gifts / Other
            elif i_id in Settings.GIFT_STATS:
                val = Settings.GIFT_STATS[i_id]
                self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + val/5)
                self.trigger_emotion("excited", 3000)
                self.window.show_emote("happy")
                self.window.create_floating_text(f"+{val // 5} ❤️", Settings.COLORS["particle_love"])
                self.sound.play("happy")
                
            # Generic fallback
            else:
                self.window.show_emote("happy")
                self.sound.play("click")
                
            if self.window_manager.inventory_win:
                self.window_manager.inventory_win.refresh()
                
    def feed(self, food_id):
        # ... logic for feeding ...
        # Simplified reusing existing logic or defining it here if missing
        if not self.is_emotion_locked:
            self.res.load_animation("eat")
            self.set_state("eat")
            self.sound.play("eat")
            self.journal.log_event("eat", details=food_id)
            QTimer.singleShot(3000, self.release_emotion)
            
        # Calc stats
        if food_id in Settings.FOOD_STATS:
            self.stats.data["hunger"] = min(100.0, self.stats.data["hunger"] + Settings.FOOD_STATS[food_id])
        elif food_id in Settings.SWEET_STATS:
            self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + Settings.SWEET_STATS[food_id])
            self.stats.data["hunger"] = min(100.0, self.stats.data["hunger"] + 5)
            
        self.window.create_floating_text("Yummy!", "#00FF00")
            


            # Force loop by relying on state, no need to stop timer since set_state handles it unless locked
            # But we are not locking emotion here to allow toggle, we just set state.
            
    def stop_dancing(self):
        if self.current_state in ["dance", "sing"]:
            anim = self.current_state
            self.set_state("idle")
            self.res.unload_animation(anim)


    def toggle_startup(self, enable):
        key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "AsunaVPet"
        exe_path = sys.executable 
        
        # If running as script, point to python w/ script
        if not getattr(sys, 'frozen', False):
             # Ensure we use pythonw to avoid console
             exe_path = f'"{sys.executable}" "{os.path.abspath("main.py")}"'
        else:
             exe_path = f'"{sys.executable}"'

        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key_handle = winreg.OpenKey(reg, key, 0, winreg.KEY_ALL_ACCESS)
            
            if enable:
                winreg.SetValueEx(key_handle, app_name, 0, winreg.REG_SZ, exe_path)
                logger.info("Added to startup.")
            else:
                try:
                    winreg.DeleteValue(key_handle, app_name)
                    logger.info("Removed from startup.")
                except FileNotFoundError:
                    pass
            
            winreg.CloseKey(key_handle)
        except Exception as e:
            logger.error(f"Startup toggle failed: {e}")
            self.window.create_floating_text("Startup Error ❌", "red")
        
    def finish_minigame(self, score):
        self.stats.data["money"] += score
        xp = score * 2
        
        self.window.create_floating_text(f"+{score} 💰", Settings.COLORS["particle_money"])
        QTimer.singleShot(1000, lambda: self.window.create_floating_text(f"+{xp} XP", Settings.COLORS["particle_xp"]))
        
        self.stats.add_xp(xp)
        self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 10)
        self.window.show_emote("happy")
        self.sound.play("happy")
        self.window.show_emote("happy")
        self.sound.play("happy")



    def set_state(self, s):
        if self.current_state == "drag" and s != "drag":
            self.sound.stop("drag")
        if self.current_state == "sleep" and s != "sleep":
            self.sound.stop("sleep")
            
        # Cooking Sound Logic (Auto-Stop/Start)
        if self.current_state == "cooking" and s != "cooking":
            self.sound.stop("cook")
        if s == "cooking" and self.current_state != "cooking":
            self.sound.start_loop("cook")
            
        if self.current_state != s: self.current_state, self.frame_index = s, 0
    def handle_click(self):
        self.reset_interaction()
        if self.current_state in ["sleep", "working"]: return
        
        now = time.time()
        self.click_count = self.click_count + 1 if now - self.last_click_time < 0.8 else 1
        self.last_click_time = now
        
        if self.click_count >= 6: self.trigger_emotion("angry", 5000); self.window.show_emote("angry"); self.sound.play("angry")
        else: self.trigger_emotion("shy", 3000); self.window.show_emote("happy"); self.check_quests("click", "pet"); self.sound.play("click")

    def talk(self, auto=False):
        """params: auto - if triggered automatically by AI"""
        key = "idle"
        
        if self.current_state == "sleep":
            key = "sleep"
        elif self.work_timer.isActive():
            key = "work"
        elif self.stats.data["hunger"] < 50:
            key = "hungry"
        elif self.stats.data["energy"] < 30:
            key = "tired"
        elif self.stats.data["happiness"] > 80:
            key = "happy"
        elif self.stats.data["happiness"] < 40:
            key = "sad"
        else:
            # Time of day based + random factor
            h = datetime.now().hour
            if 6 <= h < 12: key = "greeting_morning"
            elif 12 <= h < 18: key = "greeting_day"
            else: key = "greeting_evening"
            
            # 50/50 mix between time greeting and idle thoughts
            if random.random() < 0.5:
                # key is already set
                pass
            else:
                key = "idle"
                
        text = self._t(QUOTES[key])
        self.window.show_bubble(text)
        
        # Trigger animation if text matches specific actions
        txt_lower = text.lower()
        if "хочу співати" in txt_lower or "хочеться співати" in txt_lower or "співати!" in txt_lower:
            if not self.is_emotion_locked:
                self.res.load_animation("sing")
                self.set_state("sing")
                self.window.spawn_particles("🎵", 8, Settings.COLORS["particle_sing"])
                # Auto release after 3 seconds
                QTimer.singleShot(3000, self.release_emotion)
                
        elif "хочу танцювати" in txt_lower or "потанцювати" in txt_lower or "танцювати!" in txt_lower:
            if not self.is_emotion_locked:
                self.res.load_animation("dance")
                self.set_state("dance")
                self.window.spawn_particles("✨", 8, Settings.COLORS["particle_dance"])
                # Auto release after 3 seconds
                QTimer.singleShot(3000, self.release_emotion)

    def handle_response(self, key):
        """Handle bubble response selection."""
        if key == "happy":
            self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 15)
            self.stats.data["energy"] = min(100.0, self.stats.data["energy"] + 5)
            self.trigger_emotion("excited", 3000)
            self.window.show_emote("happy")
            self.window.create_floating_text("+15 ❤️", Settings.COLORS["particle_love"])
            self.sound.play("happy")
            
        elif key == "neutral":
            self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 5)
            self.window.show_emote("happy")
            self.window.create_floating_text("+5 ❤️", Settings.COLORS["particle_love"])
            self.window.create_floating_text("+5 ❤️", Settings.COLORS["particle_love"])
            # No sound for neutral

            
        elif key == "sad":
            self.stats.data["happiness"] = max(0, self.stats.data["happiness"] - 10)
            self.trigger_emotion("sad", 3000)
            self.window.show_emote("angry")
            self.window.create_floating_text("-10 ❤️", "#555555") # Keep separate or map to text_dark
            self.sound.play("sad")
            
        elif key.startswith("guess_"):
            # Handle Guessing Game
            # Format: "guess_{number}_{correct_number}" to be stateless? 
            # Or stateful: self.guessing_target
            
            # Using stateful approach as it's cleaner for now
            picked = key.split("_")[1]
            try:
                picked_val = int(picked)
                target = getattr(self, "guessing_target", -1)
                
                if picked_val == target:
                    # EARNED
                    self.stats.add_xp(30)
                    self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 10)
                    self.window.create_floating_text("+30 XP", "#00FF00")
                    self.window.show_emote("happy")
                    self.sound.play("happy")
                    self.window.show_bubble(self._t("games.guess_win"))
                else:
                    # LOST
                    self.stats.data["happiness"] = max(0, self.stats.data["happiness"] - 15)
                    self.window.create_floating_text("-15 ❤️", "#FF4444")
                    self.trigger_emotion("sad", 3000) # Added animation trigger
                    self.window.show_emote("sad")
                    self.sound.play("sad")
                    self.window.show_bubble(self._t("games.guess_lose", number=target))
            except ValueError:
                pass

    def start_guessing_game(self):
        target = random.randint(1, 25)
        self.guessing_target = target
        
        # Generate 2 wrong answers
        options_set = {target}
        while len(options_set) < 3:
            options_set.add(random.randint(1, 25))
            
        # Create buttons
        options_list = list(options_set)
        random.shuffle(options_list)
        
        # Prepare options for bubble: [(Label, Key)]
        ui_options = [(str(num), f"guess_{num}") for num in options_list]
        
        self.window.show_bubble(self._t("games.guess_number"), options=ui_options)

    def check_active_window(self):
        # Allow Work Check
        if self.current_state == "sleep": return

        # Global reaction cooldown (60s) for NORMAL interactions, separate for work
        
        title = window_reader.get_active_window_title().lower()
        if not title: return

        # --- POMODORO DISTRACTION CHECK ---
        if self.work_timer.isActive() or self.current_state == "working":
            # List of distracting keywords
            distractions = ["youtube", "twitch", "game", "steam", "dota", "strike", "minecraft", "instagram", "tiktok", "netflix"]
            
            if any(d in title for d in distractions):
                 # Scold user (cooldown 15s)
                 if time.time() - self.last_window_reaction_time > 15:
                     self.trigger_emotion("angry", 3000) 
                     self.window.show_emote("angry")
                     self.sound.play("angry")
                     self.window.show_bubble(self._t("dialogues.work_scold"))
                     self.last_window_reaction_time = time.time()
            return # Skip normal reactions while working

        # Ignore if busy (but allow work check above)
        if self.current_state in ["working"]: return 
        
        # Global reaction cooldown (60s)
        if time.time() - self.last_window_reaction_time < 60: return

        self.last_window_title = title
        
        # Match keywords
        found_category = None
        for category, keywords in WINDOW_KEYWORDS.items():
            if any(k in title for k in keywords):
                found_category = category
                break
        
        if found_category:
            reaction = WINDOW_REACTIONS.get(found_category)
            if reaction:
                # 30% chance to react (prevents spam even on same window)
                if random.random() < 0.3:
                    self.last_window_reaction_time = time.time()
                    
                    # Resolve text using localization
                    phrase = self._t(reaction["text"])
                    self.talk_text(phrase)
                    
                    if not self.is_emotion_locked:
                        self.trigger_emotion(reaction["anim"], 4000)

    def talk_text(self, text):
        """Directly speak a specific phrase."""
        self.window.show_bubble(text)

    def set_api_key(self, key):
        self.stats.data["gemini_api_key"] = key
        self.stats.save_stats()
        return self.ai.init_ai(key)

    def chat_with_ai(self, user_text):
        if self.ai.is_ready:
            response = self.ai.get_response(user_text)
            if response:
                self.talk_text(response)
                return True
        else:
            # Fallback if AI not ready
            self.talk_text(self._t("chat_no_conn"))
            return False

    def open_chat(self):
        from ui.chat_window import ChatWindow
        if not self.chat_win:
            self.chat_win = ChatWindow(self)
        
        if self.chat_win.isHidden():
            self.chat_win.show()
            self.chat_win.move(self.window.x() + 200, self.window.y())
        else:
            self.chat_win.hide()
            
    # Music Player Integration
    def select_music_folder(self):
        folder = QFileDialog.getExistingDirectory(None, "Виберіть папку з музикою")
        if folder:
            count = self.music_player.set_folder(folder)
            if count > 0:
                self.window.create_floating_text(self._t("music_loaded", count=count), "#00BFFF")
                self.show_music_widget()
            else:
                self.window.create_floating_text(self._t("music_empty"), "#FF4444")

    def music_volume(self, vol):
        self.music_player.set_volume(vol)
        self.window.create_floating_text(self._t("music_volume", vol=vol), "#00BFFF")
        
    def show_music_widget(self):
        from ui.music_widget import MusicWidget
        if not self.music_widget: self.music_widget = MusicWidget(self.music_player)
        self.music_widget.update_position(self.window.x(), self.window.y(), self.window.width(), self.window.height())
        self.music_widget.show()

    # System Monitor
    def toggle_system_monitor(self):
        from ui.system_widget import SystemWidget
        
        # Ensure widget exists (lazy loading)
        if not hasattr(self, 'sys_widget'):
            self.sys_widget = SystemWidget(self.sys_monitor)
            # Initial position
            self.sys_widget.move(self.window.x() - 230, self.window.y() + 50)
        
        if self.sys_widget.isVisible():
            self.sys_widget.hide()
        else:
            self.sys_widget.show()
            # Position to the left of pet
            self.sys_widget.move(self.window.x() - 230, self.window.y() + 50)
            self.sys_widget.show()

    def handle_click(self):
        self.interaction.handle_click()

    def handle_response(self, key):
        self.interaction.handle_response(key)
