from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QFrame
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
import os
from config.settings import Settings

class AchievementCard(QFrame):
    def __init__(self, key, data, unlocked):
        super().__init__()
        self.setFixedSize(260, 70)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {'rgba(40, 40, 40, 230)' if unlocked else 'rgba(20, 20, 20, 200)'};
                border: 2px solid {'#FFD700' if unlocked else '#444'};
                border-radius: 10px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Icon
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(40, 40)
        path = os.path.join(Settings.ICONS_DIR, data['icon'])
        
        if os.path.exists(path):
            pix = QPixmap(path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            if not unlocked:
                # Grayscale for locked
                img = pix.toImage()
                img.convertTo(QImage.Format.Format_Grayscale8)
                pix = QPixmap.fromImage(img)
                pix.setDevicePixelRatio(2.0)
            icon_lbl.setPixmap(pix)
        else:
            icon_lbl.setText("🏆")
            icon_lbl.setStyleSheet("color: white; font-size: 20px; border: none; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        # Details
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        name = QLabel(data['name'])
        name.setStyleSheet(f"color: {'#FFD700' if unlocked else '#888'}; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        
        desc = QLabel(data['desc'])
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {'#DDD' if unlocked else '#666'}; font-size: 10px; border: none; background: transparent;")
        
        info_layout.addWidget(name)
        info_layout.addWidget(desc)
        
        layout.addWidget(icon_lbl)
        layout.addLayout(info_layout)

class AchievementWindow(QWidget):
    def __init__(self, stats):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.container = QWidget(self)
        self.container.setStyleSheet("background: rgba(30, 30, 30, 245); border: 2px solid #FFD700; border-radius: 12px;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        
        content = QVBoxLayout(self.container)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("🏆 ДОСЯГНЕННЯ")
        title.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 14px; border: none;")
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(25, 25)
        close_btn.setStyleSheet("background: #444; color: white; border-radius: 12px; border: none; font-weight: bold;")
        close_btn.clicked.connect(self.hide)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        content.addLayout(header)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical { width: 5px; background: #222; } QScrollBar::handle:vertical { background: #555; }")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.scroll_content)
        content.addWidget(scroll)
        
        self.refresh(stats)
        self.resize(300, 400)
        
    def refresh(self, stats):
        # Clear existing
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        unlocked_ids = stats.get("achievements", [])
        
        # Sort: Unlocked first
        items = sorted(Settings.ACHIEVEMENTS.items(), key=lambda x: x[0] not in unlocked_ids)
        
        for a_id, data in items:
            unlocked = a_id in unlocked_ids
            card = AchievementCard(a_id, data, unlocked)
            self.scroll_layout.addWidget(card)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
