from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor
from datetime import datetime

class JournalWindow(QWidget):
    """UI for Asuna's Diary with a cozy, handwritten style."""
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(350, 450)

        # Main Container
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 350, 450)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #FFF9E3;
                border: 2px solid #D2B48C;
                border-radius: 15px;
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QHBoxLayout()
        title = QLabel("📖 Щоденник Асуни")
        title.setStyleSheet("color: #8B4513; font-weight: bold; font-size: 16px; border: none;")
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #D2B48C; color: white; border-radius: 15px; border: none; font-weight: bold; font-size: 18px;
            }
            QPushButton:hover { background: #A0522D; }
        """)
        close_btn.clicked.connect(self.hide)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Date Selector (Simple: Show Today for now)
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.date_lbl = QLabel(f"Дата: {today_str}")
        self.date_lbl.setStyleSheet("color: #A0522D; font-style: italic; border: none;")
        layout.addWidget(self.date_lbl)

        # Scroll Area for Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.content_lbl = QLabel()
        self.content_lbl.setWordWrap(True)
        self.content_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_lbl.setStyleSheet("""
            color: #5D4037;
            font-family: 'Segoe Print', 'Comic Sans MS', cursive;
            font-size: 13px;
            line-height: 1.5;
            border: none;
            background: transparent;
        """)
        
        scroll.setWidget(self.content_lbl)
        layout.addWidget(scroll)

        self.refresh()

    def refresh(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        text = self.manager.get_summary_text(today_str)
        self.content_lbl.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
