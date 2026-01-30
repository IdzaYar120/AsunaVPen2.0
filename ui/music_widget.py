from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class MusicWidget(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)
        
        # Style
        style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 1px solid #555;
                border-radius: 10px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover { background-color: rgba(50, 50, 50, 200); }
        """
        self.setStyleSheet(style)
        
        # Buttons
        self.btn_prev = self.create_btn("⏮️", self.player.prev_track)
        self.btn_play = self.create_btn("⏯️", self.player.toggle_pause)
        self.btn_next = self.create_btn("⏭️", self.player.next_track)
        self.btn_stop = self.create_btn("⏹️", self.stop_music)
        
        layout.addWidget(self.btn_prev)
        layout.addWidget(self.btn_play)
        layout.addWidget(self.btn_next)
        layout.addWidget(self.btn_stop)
        
        self.adjustSize()
        
    def create_btn(self, text, func):
        btn = QPushButton(text)
        btn.setFixedSize(30, 30)
        btn.clicked.connect(func)
        return btn
        
    def stop_music(self):
        self.player.stop()
        self.hide()

    def update_position(self, pet_x, pet_y, pet_w, pet_h):
        # Position below the pet
        x = pet_x + (pet_w - self.width()) // 2
        y = pet_y + pet_h + 5
        self.move(int(x), int(y))
