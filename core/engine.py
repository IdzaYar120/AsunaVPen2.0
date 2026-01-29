import random, time, logging
from PyQt6.QtCore import QTimer, QObject, QCoreApplication
from PyQt6.QtWidgets import QApplication
from core.resource_manager import ResourceManager
from core.stats_manager import StatsManager
from config.settings import Settings

logger = logging.getLogger(__name__)

class PetEngine(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.res = ResourceManager(); self.res.load_all()
        self.stats = StatsManager()
        
        # Стани та анімація
        self.current_state, self.direction, self.frame_index = "idle", 1, 0
        self.last_anim_time = time.time() * 1000
        self.is_emotion_locked = False
        self.inv_win, self.shop_win = None, None
        
        # Взаємодія
        self.click_count, self.last_click_time, self.drag_start_time = 0, 0, 0
        self.tired_remind_counter = 0
        self.last_interaction_time = time.time()

        # Таймер Pomodoro
        self.work_timer = QTimer(self); self.work_timer.timeout.connect(self.tick_work)
        self.work_seconds_left = 0
        self.current_session_mins = 0

        # Збереження при виході
        QCoreApplication.instance().aboutToQuit.connect(self.stats.save_stats)

        # Основні цикли
        self.update_timer = QTimer(self); self.update_timer.timeout.connect(self.update_loop)
        self.update_timer.start(1000 // Settings.TARGET_FPS)
        
        self.ai_timer = QTimer(self); self.ai_timer.timeout.connect(self.think)
        self.ai_timer.start(Settings.AI_THINK_INTERVAL)

    def update_loop(self):
        # Оновлення інтерфейсу
        self.window.update_stats_ui(
            self.stats.data["hunger"], self.stats.data["energy"], 
            self.stats.data["health"], self.stats.data["happiness"]
        )
        self.window.update_xp_ui(self.stats.data["xp"], self.stats.data["level"])
        
        # Розрахунок потреб з урахуванням образи
        neglected = (time.time() - self.last_interaction_time) > Settings.NEGLECT_THRESHOLD
        self.stats.update(self.current_state, neglected)

        # Пріоритети станів
        if self.window.is_dragging:
            self.handle_dragging()
        elif self.current_state == "walk" and not self.is_emotion_locked:
            self.move_pet()
        elif self.stats.data["happiness"] < Settings.HAPPINESS_THRESHOLD_SAD and not self.is_emotion_locked:
            if self.current_state not in ["sleep", "working", "training"]:
                self.set_state("sad")

        # Анімація
        now = time.time() * 1000
        if now - self.last_anim_time > Settings.ANIMATION_SPEED:
            self.update_animation(); self.last_anim_time = now
            
        self.handle_energy_logic()

    def trigger_emotion(self, state, duration):
        """АКТИВАЦІЯ ЕМОЦІЇ (Метод, який викликав помилку)"""
        self.is_emotion_locked = True
        self.set_state(state)
        QTimer.singleShot(duration, self.release_emotion)

    def release_emotion(self):
        """ПОВЕРНЕННЯ ДО НОРМАЛЬНОГО СТАНУ"""
        if self.window.is_dragging: return
        
        # Пріоритет повернення: Навчання -> Сум -> Втома -> Idle
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
        """Блокування дій, якщо Асуна нещасна"""
        if self.stats.data["happiness"] < Settings.HAPPINESS_THRESHOLD_SAD:
            self.window.show_emote("angry")
            self.window.create_floating_text("Я СУМУЮ...", "#FF4444")
            return True
        return False

    def train(self):
        if self.current_state in ["sleep", "tired", "working"]: return
        if self.check_happiness_block(): return # Перевірка настрою
        
        if self.stats.data["energy"] < 25:
            self.window.show_emote("tired"); return
            
        self.trigger_emotion("training", 4000)
        self.stats.data["energy"] -= 25
        self.stats.data["money"] += Settings.COINS_PER_TRAINING
        
        xp = Settings.XP_PER_TRAINING
        QTimer.singleShot(1000, lambda: self.window.create_floating_text(f"+{xp} XP", "#FFD700"))
        if self.stats.add_xp(xp): 
            QTimer.singleShot(4100, self.trigger_levelup)

    def trigger_levelup(self):
        self.trigger_emotion("excited", 3000)
        self.window.create_floating_text("LEVEL UP!", "#00FF00")
        self.window.show_emote("happy")

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
        self.reset_interaction()
        if i_id in Settings.GIFT_STATS:
            if self.stats.use_item(i_id):
                gain = Settings.GIFT_STATS[i_id]
                self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + gain)
                self.trigger_emotion("excited", 4000); self.window.show_emote("happy")
                self.window.create_floating_text(f"+{gain} ❤️", "#FF69B4")
        elif i_id in Settings.PLAY_ITEMS:
            if self.current_state == "sleep": return
            if self.stats.use_item(i_id):
                self.stats.data["energy"] = max(0, self.stats.data["energy"] - 15)
                self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 30)
                self.trigger_emotion("playing", 5000)
                self.window.create_floating_text("+30 ❤️", "#FF69B4")
                if self.stats.add_xp(Settings.PLAY_XP_REWARD): self.trigger_levelup()
        else: # Їжа/Солодощі
            is_sweet = i_id in Settings.SWEET_STATS
            t_stat = "energy" if is_sweet else "hunger"
            if self.stats.data[t_stat] >= 95: self.trigger_emotion("angry", 3000); self.window.show_emote("angry"); return
            if self.stats.use_item(i_id):
                gain = Settings.SWEET_STATS[i_id] if is_sweet else Settings.FOOD_STATS[i_id]
                self.stats.data[t_stat] = min(100.0, self.stats.data[t_stat] + gain)
                if is_sweet or self.current_state in ["sleep", "tired"]: self.is_emotion_locked = False
                self.trigger_emotion("eat", 5000); self.window.show_emote("happy")
        
        if self.inv_win: self.inv_win.refresh(self.stats.data)

    def handle_energy_logic(self):
        e = self.stats.data["energy"]
        if self.window.is_dragging: return
        if self.current_state == "sleep":
            self.stats.data["energy"] = min(100.0, e + 0.1)
            if self.stats.data["energy"] >= 100: self.wake_up()
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
        if random.random() < 0.3:
            self.set_state("walk"); self.direction = random.choice([1, -1])
        else: self.set_state("idle")

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

    def wake_up(self): self.is_emotion_locked = False; self.set_state("idle")
    def handle_drag_start(self): 
        if self.work_timer.isActive(): self.stop_work_session()
        self.drag_start_time = time.time(); self.is_emotion_locked = False; self.set_state("drag")
    def handle_dragging(self):
        if time.time() - self.drag_start_time > 5.0:
            if self.current_state != "angry": self.set_state("angry"); self.window.show_emote("angry")
        else: self.set_state("drag")
    def toggle_sleep(self):
        if self.current_state == "sleep": self.wake_up()
        else: self.set_state("sleep"); self.is_emotion_locked = True; self.window.show_emote("sleepy")
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
        self.is_emotion_locked = False; self.set_state("idle")
    def stop_work_session(self):
        self.work_timer.stop(); self.window.update_timer_display(None)
        self.is_emotion_locked = False; self.set_state("idle"); self.window.show_emote("angry")
    def buy_item(self, i_id, price):
        if self.stats.data["money"] >= price:
            self.stats.data["money"] -= price; inv = self.stats.data["inventory"]; inv[i_id] = inv.get(i_id, 0) + 1
            self.window.create_floating_text(f"-{price} 💰", "#FF5555"); self.window.show_emote("happy")
            if self.shop_win: self.shop_win.refresh_shop()
            if self.inv_win: self.inv_win.refresh(self.stats.data)
            return True
        else: self.window.show_emote("angry"); self.window.create_floating_text("Брак монет!", "#FF0000"); return False
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
    def set_state(self, s):
        if self.current_state != s: self.current_state, self.frame_index = s, 0
    def handle_click(self):
        self.reset_interaction()
        if self.current_state in ["sleep", "working"]: return
        now = time.time(); self.click_count = self.click_count + 1 if now - self.last_click_time < 0.8 else 1
        self.last_click_time = now
        if self.click_count >= 6: self.trigger_emotion("angry", 5000); self.window.show_emote("angry")
        else: self.trigger_emotion("shy", 3000); self.window.show_emote("happy")