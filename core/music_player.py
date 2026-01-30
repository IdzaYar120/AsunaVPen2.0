from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QDir
import os, random

class MusicPlayer:
    def __init__(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7) # 70% volume default
        
        self.playlist = []
        self.current_index = -1
        self.current_folder = ""
        
        self.player.mediaStatusChanged.connect(self.handle_media_status)
        self.player.errorOccurred.connect(self.handle_error)
        self.player.playbackStateChanged.connect(self.handle_state_change)
        
    def handle_error(self):
        print(f"Music Error: {self.player.errorString()}")
        
    def handle_state_change(self, state):
        print(f"Music State: {state}")
        
    def set_folder(self, folder_path):
        self.current_folder = folder_path
        self.playlist = []
        
        # Scan for audio files
        valid_exts = ['.mp3', '.wav', '.ogg', '.m4a']
        try:
            for f in os.listdir(folder_path):
                if any(f.lower().endswith(ext) for ext in valid_exts):
                    self.playlist.append(os.path.join(folder_path, f))
        except Exception as e:
            print(f"Error scanning folder: {e}")
            return 0
            
        if self.playlist:
            # Shuffle initially
            random.shuffle(self.playlist)
            self.current_index = 0
            self.play_current()
            return len(self.playlist)
        return 0
        
    def play_current(self):
        if not self.playlist: return
        
        path = self.playlist[self.current_index]
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        print(f"Playing: {os.path.basename(path)}")
        
    def next_track(self):
        if not self.playlist: return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_current()
        
    def prev_track(self):
        if not self.playlist: return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play_current()
        
    def stop(self):
        self.player.stop()
        
    def toggle_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()
            
    def handle_media_status(self, status):
        # Auto-play next track when finished
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_track()
            
    def set_volume(self, vol_percent):
        # vol_percent 0-100
        self.audio_output.setVolume(vol_percent / 100.0)
