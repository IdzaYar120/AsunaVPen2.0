import random, time, logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QObject, QCoreApplication
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
        self.current_state, self.direction, self.frame_index = "idle", 1, 0
        self.last_anim_time = time.time() * 1000
        self.click_count, self.last_click_time, self.drag_start_time = 0, 0, 0
        self.is_emotion_locked = False
        self.inv_win = None
        self.tired_remind_counter = 0

        # ГАРАНТОВАНЕ ЗБЕРЕЖЕННЯ ПРИ ВИХОДІ
        QCoreApplication.instance().aboutToQuit.connect(self.stats.save_stats)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_loop)
        self.update_timer.start(1000 // Settings.TARGET_FPS)
        
        self.ai_timer = QTimer(self)
        self.ai_timer.timeout.connect(self.think)
        self.ai_timer.start(Settings.AI_THINK_INTERVAL)

    def update_loop(self):
        self.window.update_stats_ui(self.stats.data["hunger"], self.stats.data["energy"], self.stats.data["health"])
        self.window.update_xp_ui(self.stats.data["xp"], self.stats.data["level"])

        if self.window.is_dragging:
            self.handle_dragging()
        elif self.current_state == "walk" and not self.is_emotion_locked:
            self.move_pet()

        now = time.time() * 1000
        if now - self.last_anim_time > Settings.ANIMATION_SPEED:
            self.update_animation(); self.last_anim_time = now
        
        self.stats.update()
        self.handle_energy_logic()

    def handle_dragging(self):
        if time.time() - self.drag_start_time > 5.0:
            if self.current_state != "angry":
                self.set_state("angry"); self.window.show_emote("angry")
        else: self.set_state("drag")

    def handle_energy_logic(self):
        energy = self.stats.data["energy"]
        if self.window.is_dragging: return

        if self.current_state == "sleep":
            self.stats.data["energy"] = min(100.0, energy + 0.1)
            if self.stats.data["energy"] >= 100: self.wake_up()
        else:
            if energy < Settings.ENERGY_THRESHOLD_SLEEP:
                self.toggle_sleep()
            elif energy < Settings.ENERGY_THRESHOLD_TIRED:
                if self.current_state != "tired" and not self.is_emotion_locked:
                    self.set_state("tired"); self.window.show_emote("tired")
                self.tired_remind_counter += 1
                if self.tired_remind_counter > (Settings.TIRED_REMIND_INTERVAL // (1000//Settings.TARGET_FPS)):
                    self.window.show_emote("tired"); self.tired_remind_counter = 0

    def wake_up(self):
        self.is_emotion_locked = False; self.set_state("idle")

    def train(self):
        if self.current_state in ["sleep", "tired"] or self.stats.data["energy"] < 25:
            self.window.show_emote("tired"); return
        self.trigger_emotion("training", 4000)
        self.stats.data["energy"] -= 25
        xp = Settings.XP_PER_TRAINING
        QTimer.singleShot(1000, lambda: self.window.create_floating_text(f"+{xp} XP"))
        if self.stats.add_xp(xp):
            QTimer.singleShot(2500, lambda: (self.window.create_floating_text("LEVEL UP!", "#00FF00"), self.window.show_emote("happy")))
        self.window.update_xp_ui(self.stats.data["xp"], self.stats.data["level"], True)

    def trigger_emotion(self, state, dur):
        self.is_emotion_locked = True; self.set_state(state)
        QTimer.singleShot(dur, self.release_emotion)

    def release_emotion(self):
        if not self.window.is_dragging and self.current_state != "sleep":
            if self.stats.data["energy"] < Settings.ENERGY_THRESHOLD_TIRED: self.set_state("tired")
            else: self.is_emotion_locked = False; self.set_state("idle")

    def use_item_from_inventory(self, i_id):
        if self.current_state == "sleep": return
        is_sweet = i_id in Settings.SWEET_STATS
        stats_map = Settings.SWEET_STATS if is_sweet else Settings.FOOD_STATS
        target_stat = "energy" if is_sweet else "hunger"

        if self.stats.data[target_stat] >= 95:
            self.trigger_emotion("angry", 3000); self.window.show_emote("angry"); return
        
        if self.stats.use_item(i_id):
            self.stats.data[target_stat] = min(100.0, self.stats.data[target_stat] + stats_map[i_id])
            self.trigger_emotion("eat", 4500); self.window.show_emote("happy")
            if is_sweet: self.wake_up()
            if self.inv_win: self.inv_win.refresh(self.stats.data)

    def update_animation(self):
        key = self.current_state
        if key == "walk": key = "walk_right" if self.direction == 1 else "walk_left"
        frames = self.res.get_frames(key)
        if frames:
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.window.render_pet(frames[self.frame_index])

    def think(self):
        if self.window.is_dragging or self.is_emotion_locked or self.current_state in ["sleep", "tired"]: return
        if random.random() < 0.3:
            self.set_state("walk"); self.direction = random.choice([1, -1])
        else: self.set_state("idle")

    def set_state(self, s):
        if self.current_state != s: self.current_state, self.frame_index = s, 0

    def move_pet(self):
        screen = QApplication.primaryScreen().geometry()
        new_x = self.window.x() + (self.direction * Settings.WALK_SPEED)
        if new_x < 10 or new_x > screen.width() - self.window.width() - 10:
            self.direction *= -1; self.set_state("idle")
        else: self.window.move(int(new_x), self.window.y())

    def open_inventory(self):
        from ui.inventory import InventoryWindow
        if not self.inv_win: self.inv_win = InventoryWindow(self.stats.data)
        self.inv_win.refresh(self.stats.data)
        self.inv_win.move(self.window.x() - self.inv_win.width() - 20, self.window.y() + 80)
        self.inv_win.show() if self.inv_win.isHidden() else self.inv_win.hide()

    def handle_drag_start(self):
        self.drag_start_time = time.time(); self.is_emotion_locked = False; self.set_state("drag")

    def handle_click(self):
        if self.current_state == "sleep": return
        now = time.time()
        self.click_count = self.click_count + 1 if now - self.last_click_time < 0.8 else 1
        self.last_click_time = now
        if self.click_count >= 6:
            self.trigger_emotion("angry", 5000); self.window.show_emote("angry")
        else: self.trigger_emotion("shy", 3000); self.window.show_emote("happy")

    def toggle_sleep(self):
        if self.current_state == "sleep": self.wake_up()
        else: self.set_state("sleep"); self.is_emotion_locked = True; self.window.show_emote("sleepy")