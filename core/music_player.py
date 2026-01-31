from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QAudioDevice
from PyQt6.QtCore import QUrl, QObject, pyqtSignal, QTimer
import os, random

class MusicPlayer(QObject):
    track_changed = pyqtSignal(str) # Emits track name
    status_changed = pyqtSignal(bool) # True = playing, False = paused
    
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self.playlist = []
        self.current_index = 0
        self.music_dir = ""
        
        # Connect signals
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        
        # Default volume
        self.audio_output.setVolume(0.5)

    def load_music_folder(self, folder_path):
        if not folder_path or not os.path.exists(folder_path): return False
        
        self.music_dir = folder_path
        self.playlist = []
        
        extensions = (".mp3", ".wav", ".ogg", ".m4a")
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(extensions):
                    self.playlist.append(os.path.join(root, file))
                    
        random.shuffle(self.playlist)
        return len(self.playlist) > 0

    def play_track(self, index):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            url = QUrl.fromLocalFile(self.playlist[self.current_index])
            self.player.setSource(url)
            self.player.play()
            
            track_name = os.path.basename(self.playlist[self.current_index])
            self.track_changed.emit(track_name)
            self.status_changed.emit(True)

    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.status_changed.emit(False)
        else:
            if not self.playlist:
                return # Do nothing if no music loaded
                
            if not self.player.source().isValid() and self.playlist:
                self.play_track(self.current_index)
            else:
                self.player.play()
                self.status_changed.emit(True)

    def next_track(self):
        if not self.playlist: return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_track(self.current_index)

    def prev_track(self):
        if not self.playlist: return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play_track(self.current_index)

    def set_volume(self, volume_0_to_1):
        self.audio_output.setVolume(volume_0_to_1)

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_track()
