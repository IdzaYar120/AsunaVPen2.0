import os
import random
from PyQt6.QtCore import QTimer
from config.settings import Settings

class EmotionManager:
    def __init__(self, engine):
        self.engine = engine
        self.stats = engine.stats
        self.window = engine.window
        self.sound = engine.sound
        self.res = engine.res
        
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
                 
        if self.engine.is_emotion_locked: return
        
        # Lazy Load Emotion
        self.res.load_animation(state)
        
        self.engine.set_state(state)
        self.engine.is_emotion_locked = True
        QTimer.singleShot(duration, self.release_emotion)

    def release_emotion(self):
        """Return to normal state after emotion ends."""
        # Return Priority: Work -> Sad -> Tired -> Idle
        if self.engine.work_timer.isActive():
            self.engine.set_state("working")
            return
            
        # Unload heavy animations if they were active
        if self.engine.current_state in ["training", "dance", "sing", "excited", "playing", "eat"]:
            self.res.unload_animation(self.engine.current_state)

        if self.stats.data["happiness"] < Settings.HAPPINESS_THRESHOLD_SAD:
            self.engine.set_state("sad")
        elif self.stats.data["energy"] < Settings.ENERGY_THRESHOLD_TIRED:
            self.engine.set_state("tired")
        else:
            self.engine.is_emotion_locked = False
            self.engine.set_state("idle")

    def check_happiness_block(self):
        """Block actions if Asuna is unhappy."""
        if self.stats.data["happiness"] < Settings.HAPPINESS_THRESHOLD_SAD:
            self.window.show_emote("angry")
            # self.window.show_emote("angry") # Removed duplicate
            self.sound.play("angry")
            self.window.create_floating_text(self.engine._t("emote_sad"), "#FF4444")
            return True
        return False
