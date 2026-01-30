from PyQt6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QTimer, QObject
import os
from config.settings import Settings

class SoundWrapper:
    def __init__(self, path, is_mp3=False):
        self.is_mp3 = is_mp3
        self.path = path
        self.effect = None
        self.player = None
        self.audio_output = None
        
        self.init_sound()

    def init_sound(self):
        url = QUrl.fromLocalFile(self.path)
        if self.is_mp3:
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.player.setSource(url)
            self.audio_output.setVolume(0.5)
        else:
            self.effect = QSoundEffect()
            self.effect.setSource(url)
            self.effect.setVolume(0.5)

    def play(self, loop=False):
        if self.is_mp3:
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.stop()
            self.player.setLoops(QMediaPlayer.Loops.Infinite if loop else 1)
            self.player.play()
        else:
            if self.effect.isPlaying():
                self.effect.stop()
            self.effect.setLoopCount(QSoundEffect.Loop.Infinite.value if loop else 1)
            self.effect.play()

    def stop(self):
        if self.is_mp3:
            self.player.stop()
        else:
            self.effect.stop()

    def is_playing(self):
        if self.is_mp3:
            return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        else:
            return self.effect.isPlaying()

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.load_sounds()
        
    def load_sounds(self):
        for name, filename in Settings.SOUNDS.items():
            path = os.path.join(Settings.SOUNDS_DIR, filename)
            if os.path.exists(path):
                is_mp3 = filename.lower().endswith('.mp3')
                self.sounds[name] = SoundWrapper(path, is_mp3)
            else:
                print(f"[WARN] Sound not found: {path}")

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play(loop=False)

    def play_looped(self, name, duration_ms):
        if name in self.sounds:
            self.sounds[name].play(loop=True)
            QTimer.singleShot(duration_ms, lambda: self.sounds[name].stop())

    def start_loop(self, name):
        if name in self.sounds:
            self.sounds[name].play(loop=True)

    def stop(self, name):
        if name in self.sounds:
            self.sounds[name].stop()
