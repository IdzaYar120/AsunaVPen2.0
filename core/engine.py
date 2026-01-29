import random
import time
from PyQt6.QtCore import QTimer, QObject
from PyQt6.QtWidgets import QApplication
from core.resource_manager import ResourceManager
from core.stats_manager import StatsManager
from config.settings import Settings

class PetEngine(QObject):
    def __init__(self, window_instance):
        super().__init__()
        self.window = window_instance
        self.res = ResourceManager()
        self.res.load_all()
        self.stats = StatsManager()
        
        self.current_state = "idle"
        self.direction = 1 
        self.frame_index = 0
        self.last_anim_time = time.time() * 1000
        
        self.click_count = 0
        self.last_click_time = 0
        self.drag_start_time = 0
        self.is_emotion_locked = False
        self.inv_win = None
        
        # Таймер для періодичного показу іконки втоми
        self.tired_remind_timer = 0 

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_loop)
        self.update_timer.start(1000 // Settings.TARGET_FPS)
        
        self.ai_timer = QTimer()
        self.ai_timer.timeout.connect(self.think)
        self.ai_timer.start(5000)

    def update_loop(self):
        self.window.update_stats_ui(self.stats.data["hunger"], self.stats.data["energy"], self.stats.data["health"])
        self.window.update_xp_ui(self.stats.data["xp"], self.stats.data["level"])

        if self.window.is_dragging:
            self.handle_dragging()
        elif self.current_state == "walk" and not self.is_emotion_locked:
            self.move_pet()

        # Оновлення кадрів
        now = time.time() * 1000
        if now - self.last_anim_time > Settings.ANIMATION_SPEED:
            self.update_animation_frame()
            self.last_anim_time = now
        
        self.stats.update()
        self.handle_energy_logic()

    def handle_dragging(self):
        duration = time.time() - self.drag_start_time
        if duration > 5.0:
            if self.current_state != "angry":
                self.set_state("angry")
                self.window.show_emote("angry")
        else:
            self.set_state("drag")

    def handle_energy_logic(self):
        """Логіка втоми: 15% - втомлена (tired.png), 5% - спить (sleepy.png)"""
        energy = self.stats.data["energy"]
        if self.window.is_dragging: return 

        if self.current_state == "sleep":
            self.stats.data["energy"] = min(100.0, energy + 0.1)
            if self.stats.data["energy"] >= 100:
                self.wake_up()
        else:
            if energy < 5.0:
                if self.current_state != "sleep":
                    self.set_state("sleep")
                    self.is_emotion_locked = True
                    self.window.show_emote("sleepy")
            elif energy < 15.0:
                # Якщо втомлена - міняємо стан
                if self.current_state != "tired" and not self.is_emotion_locked:
                    self.set_state("tired")
                    self.window.show_emote("tired")
                
                # ПЕРІОДИЧНИЙ ПОКАЗ ІКОНКИ (кожні 10 секунд, якщо вона сидить втомлена)
                self.tired_remind_timer += 1
                if self.tired_remind_timer > 600: # 600 кадрів при 60 FPS = 10 сек
                    self.window.show_emote("tired")
                    self.tired_remind_timer = 0
            else:
                self.tired_remind_timer = 0

    def train(self):
        if self.current_state in ["sleep", "tired"] or self.stats.data["energy"] < 25:
            self.window.show_emote("tired")
            return
            
        self.trigger_emotion("training", 4000)
        self.stats.data["energy"] -= 25
        xp = getattr(Settings, "XP_PER_TRAINING", 25)
        QTimer.singleShot(1000, lambda: self.window.create_floating_text(f"+{xp} XP"))
        if self.stats.add_xp(xp):
            QTimer.singleShot(2500, self.trigger_levelup)

    def trigger_levelup(self):
        self.window.create_floating_text("LEVEL UP!", color="#00FF00")
        self.window.show_emote("happy")

    def use_item_from_inventory(self, item_id):
        """Обробка використання предметів (солодощі або їжа)"""
        
        # 1. ЛОГІКА ДЛЯ СОЛОДОЩІВ (Відновлюють енергію)
        if item_id in Settings.SWEET_STATS:
            if self.stats.data["energy"] >= 100:
                self.window.show_emote("angry")
                return
                
            if self.stats.use_item(item_id):
                energy_gain = Settings.SWEET_STATS[item_id]
                self.stats.data["energy"] = min(100.0, self.stats.data["energy"] + energy_gain)
                
                # АНІМАЦІЯ: Вмикаємо стан 'eat' (вона дістає сендвіч/їсть)
                self.trigger_emotion("eat", 4000)
                self.window.show_emote("happy")
                
                # Ефект бадьорості: якщо вона спала або сиділа втомлена - прокидається
                if self.current_state in ["sleep", "tired"]:
                    self.wake_up()
                    # Додатково покажемо, що вона зраділа цукру
                    QTimer.singleShot(1000, lambda: self.window.show_emote("happy"))

        # 2. ЛОГІКА ДЛЯ ЗВИЧАЙНОЇ ЇЖІ (Відновлює голод)
        elif item_id in Settings.FOOD_STATS:
            if self.stats.data["hunger"] >= 95:
                self.window.show_emote("angry")
                return
                
            if self.stats.use_item(item_id):
                hunger_gain = Settings.FOOD_STATS[item_id]
                self.stats.data["hunger"] = min(100.0, self.stats.data["hunger"] + hunger_gain)
                
                # АНІМАЦІЯ: Вмикаємо стан 'eat'
                self.trigger_emotion("eat", 5000)
                self.window.show_emote("happy")

        # Оновлюємо вікно інвентарю, щоб кількість предметів змінилася
        if self.inv_win:
            self.inv_win.refresh(self.stats.data)
    def handle_drag_start(self):
        self.drag_start_time = time.time()
        self.is_emotion_locked = False
        self.set_state("drag")

    def release_emotion(self):
        if self.window.is_dragging: return
        if self.stats.data["energy"] < 15:
            self.set_state("tired")
            self.window.show_emote("tired") # Показуємо іконку при поверненні до втоми
        else:
            self.is_emotion_locked = False
            self.set_state("idle")

    def wake_up(self):
        self.is_emotion_locked = False
        self.set_state("idle")

    def think(self):
        if self.window.is_dragging or self.is_emotion_locked or self.current_state in ["sleep", "tired"]:
            return
        if random.random() < 0.3:
            self.set_state("walk")
            self.direction = random.choice([1, -1])
        else: self.set_state("idle")

    def handle_click(self):
        if self.current_state == "sleep": return
        now = time.time()
        self.click_count = self.click_count + 1 if now - self.last_click_time < 0.8 else 1
        self.last_click_time = now
        if self.click_count >= 6:
            self.trigger_emotion("angry", 5000); self.window.show_emote("angry")
        else: 
            self.trigger_emotion("shy", 3000)
            self.window.show_emote("happy")

    def trigger_emotion(self, state, duration):
        self.is_emotion_locked = True
        self.set_state(state)
        QTimer.singleShot(duration, self.release_emotion)

    def set_state(self, state):
        if self.current_state != state:
            self.current_state = state
            self.frame_index = 0

    def move_pet(self):
        screen = QApplication.primaryScreen().geometry()
        new_x = self.window.x() + (self.direction * Settings.WALK_SPEED)
        if new_x < 10 or new_x > screen.width() - self.window.width() - 10:
            self.direction *= -1; self.set_state("idle")
        else: self.window.move(int(new_x), self.window.y())

    def update_animation_frame(self):
        key = self.current_state
        if self.current_state == "walk":
            key = "walk_right" if self.direction == 1 else "walk_left"
        frames = self.res.get_frames(key)
        if frames:
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.window.render_pet(frames[self.frame_index])

    def open_inventory(self):
        from ui.inventory import InventoryWindow
        if not self.inv_win: self.inv_win = InventoryWindow(self.stats.data)
        self.inv_win.refresh(self.stats.data)
        self.inv_win.move(self.window.x() - self.inv_win.width() - 20, self.window.y() + 80)
        self.inv_win.show() if self.inv_win.isHidden() else self.inv_win.hide()

    def toggle_sleep(self):
        if self.current_state == "sleep": self.wake_up()
        else:
            self.set_state("sleep")
            self.is_emotion_locked = True
            self.window.show_emote("sleepy")