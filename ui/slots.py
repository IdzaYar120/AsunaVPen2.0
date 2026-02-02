from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIntValidator
import random

class SlotsWindow(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.is_spinning = False
        
        self.setWindowTitle("Casino Asuna")
        self.setFixedSize(350, 450)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Символи та коефіцієнти
        self.SYMBOLS = ["🍒", "🍋", "🍇", "💎", "👑"]
        self.WEIGHTS = [50, 25, 10, 4, 1] # Ймовірності (Баланс: частіші дрібні виграші)
        # Кеш для швидкого вибору з вагою
        self.weighted_pool = []
        for sym, w in zip(self.SYMBOLS, self.WEIGHTS):
            self.weighted_pool.extend([sym] * w)
            
        self.MULTIPLIERS = {
            "🍒": 2, "🍋": 3, "🍇": 5, "💎": 10, "👑": 50
        }

        self.init_ui()
        self.engine.sound.start_loop("slots") # Background Casino Music

    def init_ui(self):
        # Основний стиль
        self.setStyleSheet("""
            QWidget#container {
                background-color: #2b2b2b;
                border: 2px solid #FFD700;
                border-radius: 15px;
            }
            QLabel { color: white; border: none; }
            QLineEdit { 
                background: #333; color: white; border: 1px solid #555; 
                border-radius: 5px; padding: 5px; font-size: 16px; 
            }
            QPushButton {
                background-color: #FF4444; color: white;
                border: 2px solid #cc0000; border-radius: 10px;
                font-size: 20px; font-weight: bold; padding: 10px;
            }
            QPushButton:hover { background-color: #ff6666; }
            QPushButton:pressed { background-color: #cc0000; }
            QPushButton#close {
                background-color: transparent; border: none; color: #888; font-size: 16px;
            }
            QPushButton#close:hover { color: white; }
        """)

        # Контейнер
        self.container = QWidget(self); self.container.setObjectName("container")
        self.container.setGeometry(0, 0, 350, 450)
        
        layout = QVBoxLayout(self.container)
        
        # Заголовок і закриття
        top_bar = QHBoxLayout()
        title = QLabel("🎰 ASUNA SLOTS 🎰"); title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold)); title.setStyleSheet("color: #FFD700;")
        close_btn = QPushButton("❌"); close_btn.setObjectName("close"); close_btn.setFixedSize(30, 30); close_btn.clicked.connect(self.close)
        
        top_bar.addStretch()
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(close_btn)
        
        layout.addLayout(top_bar)
        
        # Баланс
        self.balance_label = QLabel("Balance: 0 💰"); self.balance_label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.balance_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Слоти
        slots_layout = QHBoxLayout()
        self.reels = []
        for _ in range(3):
            lbl = QLabel("👑"); lbl.setFont(QFont("Segoe UI Symbol", 48))
            lbl.setStyleSheet("background: #222; border: 2px solid #555; border-radius: 10px; padding: 10px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.reels.append(lbl)
            slots_layout.addWidget(lbl)
        layout.addLayout(slots_layout)
        
        # Повідомлення про виграш
        self.msg_label = QLabel("Зробіть ставку!"); self.msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_label.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.msg_label)
        
        # Ввід ставки
        bet_layout = QHBoxLayout()
        bet_layout.addWidget(QLabel("Ставка:"))
        self.bet_input = QLineEdit("10"); self.bet_input.setValidator(QIntValidator(1, 999999))
        self.bet_input.setFixedWidth(100)
        bet_layout.addWidget(self.bet_input)
        layout.addLayout(bet_layout)
        
        # Кнопка спіну
        self.spin_btn = QPushButton("SPIN!"); self.spin_btn.clicked.connect(self.spin)
        layout.addWidget(self.spin_btn)
        
        layout.addStretch()

    def update_balance(self):
        self.balance_label.setText(f"Balance: {self.engine.stats.data['money']} 💰")

    def spin(self):
        if self.is_spinning: return
        
        money = self.engine.stats.data["money"]
        try:
            bet = int(self.bet_input.text())
        except ValueError:
            self.msg_label.setText("Некоректна ставка!"); return
            
        if bet <= 0: self.msg_label.setText("Ставка має бути > 0!"); return
        if bet > money: self.msg_label.setText("Недостатньо коштів!"); return
        
        # Списання ставки
        self.engine.stats.data["money"] -= bet
        self.update_balance()
        self.msg_label.setText("Spinning...")
        
        # Анімація
        self.is_spinning = True
        self.spin_btn.setEnabled(False)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.anim_tick)
        self.anim_steps = 0
        self.anim_timer.start(50) # Faster tick for better effect
        
        self.current_bet = bet

    def anim_tick(self):
        self.anim_steps += 1
        
        # Випадковий показ символів для ефекту обертання
        for reel in self.reels:
            reel.setText(random.choice(self.SYMBOLS))
            
        if self.anim_steps >= 40: # 40 steps * 50ms = 2 seconds
            self.anim_timer.stop()
            self.finalize_spin()

    def finalize_spin(self):
        # Визначаємо результат
        res = [random.choice(self.weighted_pool) for _ in range(3)]
        
        # Set symbols
        for i, sym in enumerate(res):
            self.reels[i].setText(sym)
            
        # Check Win
        won = 0
        if res[0] == res[1] == res[2]:
            factor = self.MULTIPLIERS[res[0]]
            won = self.current_bet * factor
            self.msg_label.setText(f"JACKPOT! Виграш: {won} 💰 (x{factor})")
            self.msg_label.setStyleSheet("color: #00FF00; font-weight: bold; font-size: 16px;")
            self.engine.sound.play("happy")
        else:
            self.msg_label.setText("Спробуйте ще раз!")
            self.msg_label.setStyleSheet("color: #FF4444; font-size: 14px;")

        if won > 0:
            self.engine.stats.data["money"] += won
            self.update_balance()
            self.engine.window.create_floating_text(f"+{won} 💰", "#FFD700")

        self.is_spinning = False
        self.spin_btn.setEnabled(True)
        
        # Refresh visuals in main engine if needed
        self.engine.window.update_stats_ui(
            self.engine.stats.data["hunger"], self.engine.stats.data["energy"],
            self.engine.stats.data["health"], self.engine.stats.data["happiness"],
            self.engine.stats.get_max_stats()
        )

    def closeEvent(self, event):
        self.engine.sound.stop("slots")
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
