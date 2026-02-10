import time
import random
from config.settings import Settings

class InteractionHandler:
    def __init__(self, engine):
        self.engine = engine
        self.stats = engine.stats
        self.window = engine.window
        self.sound = engine.sound
        
    def handle_drag_start(self):
        if self.engine.work_timer.isActive(): self.engine.stop_work_session()
        self.engine.drag_start_time = time.time()
        self.engine.is_emotion_locked = False
        self.engine.set_state("drag")
        self.sound.start_loop("drag")

    def handle_dragging(self):
        if time.time() - self.engine.drag_start_time > 5.0:
            if self.engine.current_state != "angry":
                self.engine.set_state("angry")
                self.window.show_emote("angry")
                self.sound.play("angry")
        else:
            self.engine.set_state("drag")

    def handle_click(self):
        self.engine.click_count += 1
        self.engine.last_click_time = time.time()
        
        # Double Click logic could be here, but for now simple reaction
        # Or if click count logic is in engine, we just use it.
        # Engine has click_count, last_click_time state.
        
        if self.engine.click_count >= 2:
            self.engine.click_count = 0
            if self.engine.current_state == "sleep":
                self.engine.wake_up()
            else:
                self.engine.set_state("happy")
                self.window.show_emote("happy")
                self.sound.play("happy")
        else:
            # Check single click timeout elsewhere or just play sound
            self.sound.play("click")
            
    def handle_response(self, key):
        if key == "happy":
            self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 15)
            self.stats.data["energy"] = min(100.0, self.stats.data["energy"] + 5)
            self.engine.trigger_emotion("excited", 3000)
            self.window.show_emote("happy")
            self.window.create_floating_text("+15 Happy", "#FF69B4")
        elif key == "neutral":
            self.stats.data["happiness"] = min(100.0, self.stats.data["happiness"] + 5)
            self.engine.trigger_emotion("idle", 1000)
        elif key == "sad":
            self.stats.data["happiness"] = max(0.0, self.stats.data["happiness"] - 10)
            self.engine.trigger_emotion("sad", 3000)
            self.window.show_emote("sad")
        
        # Close bubble handled by validation or window
