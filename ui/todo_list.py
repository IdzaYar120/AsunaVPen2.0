from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QLabel, QFrame, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QColor, QPainter, QFont

class QuestCard(QFrame):
    def __init__(self, quest, parent_list):
        super().__init__()
        self.quest = quest
        self.parent_list = parent_list
        
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 215, 0, 100);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(5)
        
        type_icon = {"eat": "🍔", "work": "💼", "train": "⚔️", "buy": "🛒", "click": "🖱️"}.get(quest["type"], "🎲")
        
        lbl = QLabel(f"{type_icon}  {quest['text']}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: white; font-weight: bold; font-size: 13px; background: transparent; border: none;")
        
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(20, 20)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("QPushButton { color: #888; border: none; font-weight: bold; background: transparent; } QPushButton:hover { color: #FF4444; }")
        del_btn.clicked.connect(self.delete_me)
        
        header.addWidget(lbl)
        header.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)
        
        # Progress
        cur, req = quest.get("current_count", 0), quest.get("required_count", 1)
        bar = QProgressBar()
        bar.setRange(0, req)
        bar.setValue(cur)
        bar.setTextVisible(True)
        bar.setFormat(f"{cur}/{req}")
        bar.setFixedHeight(12)
        bar.setStyleSheet("""
            QProgressBar {
                background: rgba(0, 0, 0, 100);
                border-radius: 6px;
                color: white; font-size: 9px; text-align: center; border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFD700, stop:1 #FFA500);
                border-radius: 6px;
            }
        """)
        layout.addWidget(bar)
        
        # Rewards
        rewards_l = QLabel(f"+{quest['money']}💰  +{quest['xp']}XP")
        rewards_l.setStyleSheet("color: #AAA; font-size: 11px; background: transparent; border: none;")
        rewards_l.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(rewards_l)

    def delete_me(self):
        self.parent_list.delete_task(self.quest["id"])


class TodoWindow(QWidget):
    def __init__(self, task_manager, engine):
        super().__init__()
        self.task_manager = task_manager
        self.engine = engine
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(340, 500)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.old_pos = None
        self.init_ui()
        self.refresh_list()
        
    def init_ui(self):
        # Main Container (Glassmorphism)
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 340, 500)
        self.container.setStyleSheet("""
            QFrame {
                background: rgba(20, 20, 20, 240);
                border: 2px solid rgba(255, 215, 0, 100);
                border-radius: 20px;
            }
        """)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("🌟 ЩОДЕННИК")
        title.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 16px; background: transparent; border: none;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: rgba(255,255,255,100); font-size: 18px; border: none; }
            QPushButton:hover { color: white; background: rgba(255,0,0,30); border-radius: 15px; }
        """)
        close_btn.clicked.connect(self.hide)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        main_layout.addLayout(header)
        
        # Daily Progress
        self.daily_frame = QFrame()
        self.daily_frame.setStyleSheet("background: rgba(255, 255, 255, 10); border-radius: 10px; border: none;")
        d_layout = QVBoxLayout(self.daily_frame)
        
        self.daily_lbl = QLabel("Щоденний прогрес: 0/5")
        self.daily_lbl.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background: transparent;")
        
        self.daily_bar = QProgressBar()
        self.daily_bar.setRange(0, 5)
        self.daily_bar.setFixedHeight(8)
        self.daily_bar.setTextVisible(False)
        self.daily_bar.setStyleSheet("""
            QProgressBar { background: rgba(0,0,0,100); border-radius: 4px; border: none; }
            QProgressBar::chunk { background: #00FF00; border-radius: 4px; }
        """)
        
        d_layout.addWidget(self.daily_lbl)
        d_layout.addWidget(self.daily_bar)
        main_layout.addWidget(self.daily_frame)
        
        # Scroll Area for Quests
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(0, 0, 5, 0)
        
        self.scroll.setWidget(self.list_container)
        main_layout.addWidget(self.scroll)

    def refresh_list(self):
        # Update Daily Progress
        count = self.engine.stats.data.get("daily_tasks_completed", 0)
        self.daily_bar.setValue(min(5, count))
        self.daily_lbl.setText(f"Щоденний прогрес: {count}/5" + (" (BONUS!)" if count >= 5 else ""))
        
        # Clear List
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        quests = self.task_manager.stats.data.get("tasks", [])
        
        if not quests:
            lbl = QLabel("Поки що немає завдань...\nАсуна думає 🤔")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: rgba(255,255,255,100); font-style: italic; margin-top: 50px; background: transparent; border: none;")
            self.list_layout.addWidget(lbl)
            return

        for q in quests:
            card = QuestCard(q, self)
            self.list_layout.addWidget(card)

    def delete_task(self, task_id):
        self.task_manager.remove_task(task_id)
        self.refresh_list()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
