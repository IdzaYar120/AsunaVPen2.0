import random, time, logging
from PyQt6.QtCore import QTimer, QObject, QCoreApplication
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtMultimedia import QMediaPlayer
from core.resource_manager import ResourceManager
from core.stats_manager import StatsManager
from core.task_manager import TaskManager
from core.sound_manager import SoundManager
from core.dialogues import QUOTES, WINDOW_KEYWORDS, WINDOW_REACTIONS
from core import window_reader
from config.settings import Settings
from datetime import datetime
from ui.minigame import CoinGameWindow
from ui.slots import SlotsWindow
from ui.todo_list import TodoWindow
from ui.shop import ShopWindow
from ui.inventory import InventoryWindow
from ui.inventory import InventoryWindow
from ui.achievements import AchievementWindow
from ui.achievements import AchievementWindow
from core.ai_client import AIClient
from core.music_player import MusicPlayer
from PyQt6.QtWidgets import QFileDialog

logger = logging.getLogger(__name__)

class PetEngine(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.res = ResourceManager(); self.res.load_all()
        self.stats = StatsManager()
        self.task_manager = TaskManager(self.stats)
        self.sound = SoundManager()
        
        self.ai = AIClient()
        if self.stats.data.get("gemini_api_key"):
            self.ai.init_ai(self.stats.data["gemini_api_key"])
            
        
        self.music_player = MusicPlayer()
        
        # System Monitor (Background)
        from core.system_monitor import SystemMonitor
        self.sys_monitor = SystemMonitor()

        
        # States and Animation
        self.current_state, self.direction, self.frame_index = "idle", 1, 0
        self.last_anim_time = time.time() * 1000
        self.is_emotion_locked = False
        self.current_state, self.direction, self.frame_index = "idle", 1, 0
        self.last_anim_time = time.time() * 1000
        self.is_emotion_locked = False
        self.inv_win, self.shop_win, self.todo_win, self.minigame_win, self.slots_win, self.chat_win = None, None, None, None, None, None
        self.ach_win = None # Initialize AchievementWindow
        self.music_widget = None
        self.last_window_title = ""
        self.last_window_check = 0
        self.last_window_reaction_time = 0
        
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
        
        # Achievement Check (every 3s for optimization)
        if int(time.time()) % 3 == 0:
            self.check_achievements()
            
        # Active Window Check (every 5s)
        if time.time() - self.last_window_check > 5:
            self.check_active_window()
            self.last_window_check = time.time()

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
        if self.music_widget and self.music_widget.isVisible():
            self.music_widget.update_position(self.window.x(), self.window.y(), self.window.width(), self.window.height())
            
        self.handle_energy_logic()

    def trigger_emotion(self, state, duration):
        # Special Logic for Dance (Music Reaction) - Support for Sing/Dance + Rewards
        if state == "dance":
             options = []
             if self.res.get_frames("dance"): options.append("dance")
             if self.res.get_frames("sing"): options.append("sing")
             
             if options:
                 state = random.choice(options)
                 # Rewards & Visuals
                 reward = Settings.DANCE_XP_REWARD
                 self.stats.add_xp(reward)
                 self.window.create_floating_text(f"+{reward} XP", "#00FF00")
                 particle = "✨" if state == "dance" else "🎵"
                 p_color = "#FFD700" if state == "dance" else "#00BFFF"
                 self.window.spawn_particles(particle, 8, p_color)
                 
        if self.is_emotion_locked: return
        self.set_state(state)
        self.is_emotion_locked = True
        QTimer.singleShot(duration, self.release_emotion)

    def release_emotion(self):
        """Return to normal state after emotion ends."""
        if self.window.is_dragging: return
        
        # Return Priority: Work -> Sad -> Tired -> Idle
        if self.work_timer.isActive():
            self.set_state("working")
            return
            
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
            self.window.create_floating_text("Я СУМУЮ...", "#FF4444")
            return True
        return False

    def train(self):
        if self.current_state in ["sleep", "tired", "working"] or self.is_emotion_locked: return
        if self.check_happiness_block(): return # Mood Check
        
        if self.stats.data["energy"] < 25:
            self.window.show_emote("tired"); return
            
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

    def check_quests(self, event_type, value, delay_victory=0):
        rewards = self.task_manager.check_event(event_type, value)
        for r in rewards:
            # Apply rewards immediately
            self.stats.data["money"] += r["money"]
            self.stats.add_xp(r["xp"])
            hap = r.get("happiness", 10)
            self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + hap)
            
            # Delayed animation and text
            QTimer.singleShot(delay_victory, lambda: self.window.create_floating_text("КВЕСТ ВИКОНАНО!", "#00FF00"))
            QTimer.singleShot(delay_victory + 500, lambda r=r: self.window.create_floating_text(f"+{r['money']} 💰  +{r['xp']} XP", "#FFD700"))
            QTimer.singleShot(delay_victory + 1500, lambda h=hap: self.window.create_floating_text(f"+{h} ❤️", "#FF69B4"))
            
            QTimer.singleShot(delay_victory, lambda: self.trigger_emotion("excited", 4000))
            QTimer.singleShot(delay_victory, lambda: self.sound.play("happy"))
        
        # Always update list to reflect progress
        if self.todo_win and not self.todo_win.isHidden(): self.todo_win.refresh_list()


    def trigger_levelup(self):
        # Level Up Reward
        reward = Settings.LEVEL_UP_REWARD_COINS
        self.stats.data["money"] += reward
        
        self.trigger_emotion("excited", 4000)
        self.window.create_floating_text(f"LEVEL UP! {self.stats.data['level']}", "#00FF00")
        QTimer.singleShot(1500, lambda: self.window.create_floating_text(f"+{reward} 💰", "#FFD700"))
        
        self.window.show_emote("happy")
        self.sound.play("happy")

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
        if self.is_emotion_locked: return
        self.reset_interaction()
        if i_id in Settings.GIFT_STATS:
            if self.stats.use_item(i_id):
                gain = Settings.GIFT_STATS[i_id]
                self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + gain)
                self.trigger_emotion("excited", 4000); self.window.show_emote("happy"); self.sound.play("arigato")
                self.window.create_floating_text(f"+{gain} ❤️", "#FF69B4")
                self.check_quests("eat", i_id, delay_victory=4000) # Gift treated as eat/use
        elif i_id in Settings.PLAY_ITEMS:
            if self.current_state == "sleep": return
            if self.stats.use_item(i_id):
                self.stats.data["energy"] = max(0, self.stats.data["energy"] - 15)
                self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 30)
                self.trigger_emotion("playing", 5000)
                self.window.create_floating_text("+30 ❤️", "#FF69B4")
                if self.stats.add_xp(Settings.PLAY_XP_REWARD): self.trigger_levelup()
        else: # Food / Sweets
            is_sweet = i_id in Settings.SWEET_STATS
            t_stat = "energy" if is_sweet else "hunger"
            max_val = self.stats.get_max_stats()
            
            if self.stats.data[t_stat] >= max_val - 5: 
                self.trigger_emotion("angry", 3000); self.window.show_emote("angry"); self.sound.play("angry"); return
                
            if self.stats.use_item(i_id):
                gain = Settings.SWEET_STATS[i_id] if is_sweet else Settings.FOOD_STATS[i_id]
                self.stats.data[t_stat] = min(max_val, self.stats.data[t_stat] + gain)
                
                # Sweets add a little happiness
                if is_sweet:
                    self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 5)
                    self.window.create_floating_text("+5 ❤️", "#FF69B4")
                
                if is_sweet or self.current_state in ["sleep", "tired"]: self.is_emotion_locked = False
                self.trigger_emotion("eat", 5000); self.window.show_emote("happy"); self.sound.play_looped("eat", 5000)
                self.check_quests("eat", i_id, delay_victory=5000)
        
        if self.inv_win: self.inv_win.refresh(self.stats.data)

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

    def check_system_reactions(self):
        if not hasattr(self, 'sys_monitor'): return
        
        stats = self.sys_monitor.get_stats()
        
        # High CPU Reaction
        if stats["cpu"] > 80:
            self.trigger_emotion("tired", 4000)
            self.talk_text(random.choice([
                "Ух... процесор кипить! 🔥",
                "Мені аж жарко стало... 🥵",
                "Комп'ютер зараз злетить! 🚀"
            ]))
            return

        # Low Battery Reaction
        if stats["battery"] is not None and stats["battery"] < 20 and not stats["plugged"]:
            self.trigger_emotion("scared", 4000)
            self.talk_text("Ей! Заряджай нас швидше! 🔋😱")
            return
            
        # High RAM Reaction
        if stats["ram_percent"] > 90:
             self.trigger_emotion("confused", 4000)
             self.talk_text("Ого, пам'яті зовсім немає... 😵‍💫")
        
        # Chance for new quest (5% every 5s approx)
        if random.random() < 0.05:
            if self.task_manager.generate_random_quest():
                self.window.show_emote("quest")
                self.sound.play("quest")
                if self.todo_win and not self.todo_win.isHidden(): self.todo_win.refresh_list()
        
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
        if not self.ach_win:
            self.ach_win = AchievementWindow(self.stats.data)
        self.ach_win.refresh(self.stats.data)
        self.window.position_window(self.ach_win)
        self.ach_win.show()

    def check_achievements(self):
        # 1. Level
        if self.stats.data["level"] >= 5: self._try_unlock("level_5")
        if self.stats.data["level"] >= 10: self._try_unlock("level_10")
        if self.stats.data["level"] >= 20: self._try_unlock("level_20")
            
        # 2. Money
        if self.stats.data["money"] >= 1000: self._try_unlock("rich")
        if self.stats.data["money"] >= 5000: self._try_unlock("tycoon")
            
        # 3. Best Friend
        if self.stats.data["happiness"] >= 99.9: self._try_unlock("best_friend")
            
        # 4. Games
        games = self.stats.data.get("games_played", 0)
        if games >= 10: self._try_unlock("gamer")
        if games >= 50: self._try_unlock("pro_gamer")
            
        # 5. Work
        worked = self.stats.data.get("minutes_worked", 0)
        if worked >= 60: self._try_unlock("worker")
        if worked >= 300: self._try_unlock("manager")
        
        # 6. Hoarder (Inventory Count)
        total_items = sum(self.stats.data.get("inventory", {}).values())
        if total_items >= 20: self._try_unlock("hoarder")

    def _try_unlock(self, a_id):
        if self.stats.unlock_achievement(a_id):
            info = Settings.ACHIEVEMENTS[a_id]
            self.window.show_achievement_popup(info["name"], info["icon"])
            self.sound.play("happy") # Звук успіху

    def wake_up(self): 
        self.is_emotion_locked = False; self.set_state("idle")
        self.sound.stop("sleep")
    def handle_drag_start(self): 
        if self.work_timer.isActive(): self.stop_work_session()
        self.drag_start_time = time.time(); self.is_emotion_locked = False; self.set_state("drag")
        self.sound.start_loop("drag")
    def handle_dragging(self):
        if time.time() - self.drag_start_time > 5.0:
            if self.current_state != "angry": self.set_state("angry"); self.window.show_emote("angry"); self.sound.play("angry")
        else: self.set_state("drag")
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
        self.is_emotion_locked = False; self.set_state("idle")
    def stop_work_session(self):
        self.work_timer.stop(); self.window.update_timer_display(None)
        self.is_emotion_locked = False; self.set_state("idle"); self.window.show_emote("angry"); self.sound.play("angry")
    def buy_item(self, i_id, price):
        if self.stats.data["money"] >= price:
            self.stats.data["money"] -= price; inv = self.stats.data["inventory"]; inv[i_id] = inv.get(i_id, 0) + 1
            self.window.create_floating_text(f"-{price} 💰", "#FF5555"); self.window.show_emote("happy")
            self.check_quests("buy", i_id)
            if self.shop_win: self.shop_win.refresh_shop()
            if self.inv_win: self.inv_win.refresh(self.stats.data)
            return True
        else: self.window.show_emote("angry"); self.window.create_floating_text("Брак монет!", "#FF0000"); self.sound.play("angry"); return False
    def open_inventory(self):
        from ui.inventory import InventoryWindow
        if not self.inv_win: self.inv_win = InventoryWindow(self.stats.data)
        self.inv_win.refresh(self.stats.data); self.inv_win.move(self.window.x() - self.inv_win.width() - 20, self.window.y() + 80); self.inv_win.show() if self.inv_win.isHidden() else self.inv_win.hide()
    def open_shop(self):
        from ui.shop import ShopWindow
        if not self.shop_win: self.shop_win = ShopWindow(self)
        if self.shop_win.isHidden():
            self.shop_win.refresh_shop(); screen = QApplication.primaryScreen().availableGeometry()
            nx = max(screen.left()+10, min(self.window.x()-100, screen.right()-self.shop_win.width()-10))
            ny = max(screen.top()+10, min(self.window.y()-self.shop_win.height()-10, screen.bottom()-self.shop_win.height()-10))
            self.shop_win.move(int(nx), int(ny)); self.shop_win.show()
        else: self.shop_win.hide()
        
    def open_todo_list(self):
        from ui.todo_list import TodoWindow
        if not self.todo_win:
            self.todo_win = TodoWindow(self.task_manager)
        
        if self.todo_win.isHidden():
            self.todo_win.refresh_list()
            self.todo_win.move(self.window.x() + self.window.width() + 20, self.window.y())
            self.todo_win.show()
        else: self.todo_win.hide()
        
    def open_minigame(self):
        from ui.minigame import CoinGameWindow
        if self.minigame_win is None or not self.minigame_win.isVisible():
            self.minigame_win = CoinGameWindow(self)
            self.minigame_win.move(self.window.x(), self.window.y() - 320)
            self.minigame_win.show()
            
    def finish_minigame(self, score):
        self.stats.data["money"] += score
        xp = score * 2
        
        self.window.create_floating_text(f"+{score} 💰", "#FFD700")
        QTimer.singleShot(1000, lambda: self.window.create_floating_text(f"+{xp} XP", "#00FF00"))
        
        self.stats.add_xp(xp)
        self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 10)
        self.window.show_emote("happy")
        self.sound.play("happy")
        self.minigame_win = None

    def open_slots(self):
        from ui.slots import SlotsWindow
        if self.slots_win is None or not self.slots_win.isVisible():
            self.slots_win = SlotsWindow(self)
            self.slots_win.move(self.window.x(), self.window.y() - 320)
            self.slots_win.show()
            self.sound.play("slots")


    def set_state(self, s):
        if self.current_state == "drag" and s != "drag":
            self.sound.stop("drag")
        if self.current_state == "sleep" and s != "sleep":
            self.sound.stop("sleep")
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
        if self.current_state == "sleep":
            text = random.choice(QUOTES["sleep"])
        elif self.work_timer.isActive():
            text = random.choice(QUOTES["work"])
        elif self.stats.data["hunger"] < 50:
            text = random.choice(QUOTES["hungry"])
        elif self.stats.data["energy"] < 30:
            text = random.choice(QUOTES["tired"])
        elif self.stats.data["happiness"] > 80:
            text = random.choice(QUOTES["happy"])
        elif self.stats.data["happiness"] < 40:
            text = random.choice(QUOTES["sad"])
        else:
            # Time of day based + random factor
            h = datetime.now().hour
            if 6 <= h < 12: key = "greeting_morning"
            elif 12 <= h < 18: key = "greeting_day"
            else: key = "greeting_evening"
            
            # 50/50 mix between time greeting and idle thoughts
            if random.random() < 0.5:
                text = random.choice(QUOTES[key])
            else:
                text = random.choice(QUOTES["idle"])
                
        self.window.show_bubble(text)

    def handle_response(self, key):
        """Handle bubble response selection."""
        if key == "happy":
            self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 15)
            self.stats.data["energy"] = min(100.0, self.stats.data["energy"] + 5)
            self.trigger_emotion("excited", 3000)
            self.window.show_emote("happy")
            self.window.create_floating_text("+15 ❤️", "#FF69B4")
            self.sound.play("happy")
            
        elif key == "neutral":
            self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 5)
            self.window.show_emote("happy")
            self.window.create_floating_text("+5 ❤️", "#FF69B4")
            self.window.create_floating_text("+5 ❤️", "#FF69B4")
            # No sound for neutral

            
        elif key == "sad":
            self.stats.data["happiness"] = max(0, self.stats.data["happiness"] - 10)
            self.trigger_emotion("sad", 3000)
            self.window.show_emote("angry")
            self.window.create_floating_text("-10 ❤️", "#555555")
            self.sound.play("sad")

    def check_active_window(self):
        # Ignore if pet is busy (sleeping/working)
        if self.current_state in ["sleep", "working"]: return
        
        # Global reaction cooldown (60s)
        if time.time() - self.last_window_reaction_time < 60: return

        title = window_reader.get_active_window_title().lower()
        if not title: return
        
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
                    
                    # Resolve text: list or string
                    texts = reaction["text"]
                    phrase = random.choice(texts) if isinstance(texts, list) else texts
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
            self.talk_text("Я... не маю з'єднання з космосом (Інтернетом). 📡\n(Перевір API ключ або підключення)")
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
            self.music_player.load_music(folder)
            self.music_player.play_music()
            self.window.create_floating_text("Музика завантажена! 🎵", "#00BFFF")
            self.show_music_widget()

    def music_volume(self, vol):
        self.music_player.set_volume(vol)
        self.window.create_floating_text(f"Гучність: {vol}%", "#00BFFF")
        
    def show_music_widget(self):
        from ui.music_widget import MusicWidget
        if not self.music_widget: self.music_widget = MusicWidget(self.music_player)
        self.music_widget.update_position(self.window.x(), self.window.y(), self.window.width(), self.window.height())
        self.music_widget.show()

    # System Monitor
    def toggle_system_monitor(self):
        from core.system_monitor import SystemMonitor
        from ui.system_widget import SystemWidget
        
        if not hasattr(self, 'sys_monitor'):
            self.sys_monitor = SystemMonitor()
            self.sys_widget = SystemWidget(self.sys_monitor)
        
        if self.sys_widget.isVisible():
            self.sys_widget.hide()
        else:
            # Position to the left of pet
            self.sys_widget.move(self.window.x() - 230, self.window.y() + 50)
            self.sys_widget.show()
