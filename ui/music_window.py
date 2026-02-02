from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QFrame, QSlider
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter

import random
from config.settings import Settings

class VisualizerBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(8)
        self.setFixedHeight(10)
        self.setStyleSheet("background-color: #FFD700; border-radius: 4px;")
        
    def set_height(self, h):
        self.setFixedHeight(max(5, h))
        # Color gradient based on height
        if h > 80: color = "#FF0000"
        elif h > 50: color = "#FFD700"
        else: color = "#00FF00"
        self.setStyleSheet(f"background-color: {color}; border-radius: 4px;")

class MusicWindow(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.player = engine.music_player
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 180)
        
        # Connect player signals
        # Connect player signals
        self.player.track_changed.connect(self.update_track_info)
        self.player.status_changed.connect(self.update_play_btn)
        
        # Visualizer Timer
        self.viz_timer = QTimer(self)
        self.viz_timer.timeout.connect(self.update_visualizer)
        self.bars = []
        
        self.init_ui()
        
    def init_ui(self):
        # Container
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 320, 180)
        self.container.setStyleSheet("""
            QFrame {
                background: rgba(20, 20, 20, 220);
                border: 2px solid #00FFFF;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(self.container)
        
        # Header (Track Name)
        self.track_lbl = QLabel("🎵 No Music Selected")
        self.track_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_lbl.setStyleSheet("color: white; font-weight: bold; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(self.track_lbl)
        
        # Visualizer Area
        viz_layout = QHBoxLayout()
        viz_layout.setSpacing(2)
        viz_layout.addStretch()
        for _ in range(15): # 15 bars
            bar = VisualizerBar()
            self.bars.append(bar)
            viz_layout.addWidget(bar, alignment=Qt.AlignmentFlag.AlignBottom)
        viz_layout.addStretch()
        layout.addLayout(viz_layout)
        
        # Controls
        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addStretch()
        
        btn_style = """
            QPushButton {
                background: rgba(255,255,255,20);
                border: 1px solid rgba(255,255,255,50);
                border-radius: 15px;
                color: white; font-size: 16px;
            }
            QPushButton:hover { background: rgba(255,255,255,40); }
        """
        
        self.folder_btn = QPushButton("📂")
        self.folder_btn.setFixedSize(30,30); self.folder_btn.setStyleSheet(btn_style)
        self.folder_btn.clicked.connect(self.select_folder)
        
        self.prev_btn = QPushButton("⏮️")
        self.prev_btn.setFixedSize(30,30); self.prev_btn.setStyleSheet(btn_style)
        self.prev_btn.clicked.connect(self.player.prev_track)
        
        self.play_btn = QPushButton("▶️")
        self.play_btn.setFixedSize(40,40)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #00FFFF; border-radius: 20px; color: black; font-size: 20px;
            }
            QPushButton:hover { background: #E0FFFF; }
        """)
        self.play_btn.clicked.connect(self.player.toggle_playback)
        
        self.next_btn = QPushButton("⏭️")
        self.next_btn.setFixedSize(30,30); self.next_btn.setStyleSheet(btn_style)
        self.next_btn.clicked.connect(self.player.next_track)
        
        self.close_btn = QPushButton("❌")
        self.close_btn.setFixedSize(30,30); self.close_btn.setStyleSheet(btn_style)
        self.close_btn.setFixedSize(30,30); self.close_btn.setStyleSheet(btn_style)
        self.close_btn.clicked.connect(self.request_dock)
        
        controls.addWidget(self.folder_btn)
        controls.addWidget(self.prev_btn)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.next_btn)
        controls.addWidget(self.close_btn)
        controls.addStretch()
        
        # Volume Slider
        vol_layout = QHBoxLayout()
        vol_layout.setContentsMargins(10, 0, 10, 5)
        lbl_vol = QLabel("🔊")
        lbl_vol.setStyleSheet("color: white; font-size: 14px; border:none; background:transparent;")
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(Settings.VOLUME_MUSIC)
        self.slider_vol.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #555; border-radius: 2px; }
            QSlider::handle:horizontal { background: #00FFFF; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
        """)
        self.slider_vol.valueChanged.connect(self.on_volume_change)
        
        vol_layout.addWidget(lbl_vol)
        vol_layout.addWidget(self.slider_vol)
        
        layout.addLayout(controls)
        layout.addLayout(vol_layout)

    def request_dock(self):
        # Trigger engine to dock to mini-player
        if hasattr(self.engine, "dock_music_player"):
            self.engine.dock_music_player()
        else:
            self.close()

    def on_volume_change(self, val):
        Settings.VOLUME_MUSIC = val
        self.player.set_volume(val / 100.0)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Виберіть папку з музикою")
        if folder:
            count = self.player.load_music_folder(folder)
            if count:
                self.player.play_track(0)
                self.viz_timer.start(50) # Start visualizer
                self.engine.window.create_floating_text("Музика завантажена! 🎧", "#00FFFF")
            else:
                self.engine.window.create_floating_text("Файлів не знайдено 😔", "#FF0000")

    def update_track_info(self, name):
        # Truncate if too long
        if len(name) > 35: name = name[:32] + "..."
        self.track_lbl.setText(f"🎵 {name}")
        
    def update_play_btn(self, is_playing):
        self.play_btn.setText("⏸️" if is_playing else "▶️")
        if is_playing:
            self.viz_timer.start(50)
            self.engine.start_dancing() # Trigger dance in engine
        else:
            self.viz_timer.stop()
            self.reset_visualizer()
            self.engine.stop_dancing()

    def update_visualizer(self):
        # Simulate frequency data since QMediaPlayer doesn't expose it easily
        for bar in self.bars:
            h = random.randint(10, 80)
            bar.set_height(h)

    def reset_visualizer(self):
        for bar in self.bars:
            bar.set_height(5)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
