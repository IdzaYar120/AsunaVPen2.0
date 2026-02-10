from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
import os
from config.settings import Settings

class MailWindow(QWidget):
    """A popup window for reading letters from friends."""
    def __init__(self, engine, mail_data):
        super().__init__()
        self.engine = engine
        self.mail_data = mail_data
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 220)

        # Main Container
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 320, 220)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border: 2px solid #FFD700;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self.container)
        
        # Header (Sender)
        header = QHBoxLayout()
        sender_lbl = QLabel(f"📨 Лист від: {mail_data['sender_name']}")
        sender_lbl.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 14px; border: none;")
        header.addWidget(sender_lbl)
        layout.addLayout(header)

        # Message Body
        self.msg_lbl = QLabel(mail_data['text'])
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("color: #EEE; font-size: 12px; border: none; font-style: italic;")
        layout.addWidget(self.msg_lbl)

        # Gift Info
        gift_layout = QHBoxLayout()
        gift_icon = QLabel("🎁")
        gift_icon.setStyleSheet("font-size: 18px; border: none;")
        
        # Resolve item name (localized if possible)
        gift_name = mail_data['gift_item'].replace("-", " ").title()
        gift_lbl = QLabel(f"Подарунок: {gift_name}")
        gift_lbl.setStyleSheet("color: #00FF00; font-weight: bold; border: none;")
        
        gift_layout.addWidget(gift_icon)
        gift_layout.addWidget(gift_lbl)
        gift_layout.addStretch()
        layout.addLayout(gift_layout)

        # Claim Button
        self.claim_btn = QPushButton("ПРИЙНЯТИ")
        self.claim_btn.setFixedSize(120, 35)
        self.claim_btn.setStyleSheet("""
            QPushButton {
                background: #FFD700; color: #222; border-radius: 8px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: #DAA520; }
        """)
        self.claim_btn.clicked.connect(self.claim_gift)
        
        btn_center = QHBoxLayout()
        btn_center.addStretch()
        btn_center.addWidget(self.claim_btn)
        btn_center.addStretch()
        layout.addLayout(btn_center)

    def claim_gift(self):
        item_id = self.mail_data['gift_item']
        self.engine.stats.add_item(item_id)
        self.engine.window.create_floating_text(f"+1 {item_id}", "#00FF00")
        self.engine.sound.play("happy")
        
        # Log to journal
        if hasattr(self.engine, 'journal'):
            self.engine.journal.log_event("mail", details=f"Отримала подарунок від {self.mail_data['sender_name']}")
            
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
