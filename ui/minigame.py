from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QCursor
import random
from config.settings import Settings

class CoinGameWindow(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.score = 0
        self.time_left = Settings.MINIGAME_DURATION
        
        self.setWindowTitle("Полювання за монетами!")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Стилізація
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 220);
                border-radius: 15px;
                border: 2px solid #FFD700;
            }
            QLabel {
                color: white;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            QPushButton {
                background-color: #FFD700;
                border: 2px solid white;
                border-radius: 20px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #FFC000;
            }
            QPushButton:pressed {
                background-color: #FFA500;
            }
        """)
        
        self.init_ui()
        
        # Таймер гри
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.tick)
        self.game_timer.start(1000)
        
        self.spawn_coin()
        self.engine.sound.start_loop("coin_game")

    def init_ui(self):
        # Рахунок
        self.score_label = QLabel(f"Score: 0", self)
        self.score_label.setGeometry(20, 20, 150, 30)
        self.score_label.setFont(QFont("Segoe UI", 12))
        
        # Час
        self.time_label = QLabel(f"Time: {self.time_left}", self)
        self.time_label.setGeometry(300, 20, 80, 30)
        self.time_label.setFont(QFont("Segoe UI", 12))
        
        # Кнопка-монетка
        self.coin_btn = QPushButton("💰", self)
        self.coin_btn.setFixedSize(50, 50)
        self.coin_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.coin_btn.clicked.connect(self.catch_coin)

    def spawn_coin(self):
        # Випадкова позиція всередині вікна (з відступами)
        x = random.randint(20, 330)
        y = random.randint(60, 230)
        self.coin_btn.move(x, y)

    def catch_coin(self):
        self.score += Settings.COIN_REWARD
        self.score_label.setText(f"Score: {self.score}")
        self.spawn_coin()
        # self.engine.sound.play("click") 

    def tick(self):
        self.time_left -= 1
        self.time_label.setText(f"Time: {self.time_left}")
        if self.time_left <= 0:
            self.end_game()

    def end_game(self):
        self.game_timer.stop()
        self.engine.sound.stop("coin_game")
        self.engine.finish_minigame(self.score)
        self.close()
