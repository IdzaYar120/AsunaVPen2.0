from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QImage
import os
from config.settings import Settings

class ShopItem(QWidget):
    def __init__(self, item_id, price, level, on_buy_callback):
        super().__init__()
        # ФІКС: Фіксований розмір картки товару
        self.setFixedSize(80, 100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Перевірка блокування
        req_level = Settings.SHOP_UNLOCKS.get(item_id, 1)
        is_locked = level < req_level
        
        path = os.path.join(Settings.ICONS_DIR, f"{item_id}.png")
        icon = QLabel()
        if os.path.exists(path):
            pix = QPixmap(path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            if is_locked:
                # Ефект сірого
                img = pix.toImage()
                img.convertTo(QImage.Format.Format_Grayscale8)
                pix = QPixmap.fromImage(img)
                pix.setDevicePixelRatio(2.0) # Для чіткості
            icon.setPixmap(pix)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        info_text = f"{item_id.replace('-', ' ').title()}\n💰 {price}"
        if is_locked: info_text = f"Lvl {req_level}\n🔒"
        
        info = QLabel(info_text)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet(f"color: {'#888' if is_locked else 'white'}; font-size: 9px; font-weight: bold; border: none;")
        
        btn = QPushButton("Купити")
        btn.setFixedSize(70, 20)
        if is_locked:
            btn.setText(f"Lvl {req_level}")
            btn.setEnabled(False)
            btn.setStyleSheet("background: #555; color: #AAA; border-radius: 4px; font-size: 10px;")
        else:
            btn.setStyleSheet("background: #2E7D32; color: white; border-radius: 4px; font-size: 10px;")
            btn.clicked.connect(lambda: on_buy_callback(item_id, price))
        
        layout.addWidget(icon)
        layout.addWidget(info)
        layout.addWidget(btn)

class ShopWindow(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.drag_pos = None
        
        container = QWidget(self)
        container.setStyleSheet("background: rgba(30, 30, 30, 245); border: 2px solid #FFD700; border-radius: 12px;")
        self.main_vbox = QVBoxLayout(self)
        self.main_vbox.addWidget(container)
        
        content = QVBoxLayout(container)
        header = QHBoxLayout()
        title = QLabel("МАГАЗИН"); title.setStyleSheet("color: #FFD700; font-weight: bold; border: none;")
        self.balance = QLabel(); self.balance.setStyleSheet("color: white; font-weight: bold; border: none;")
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("background: #444; color: white; border-radius: 10px; border: none;")
        close_btn.clicked.connect(self.hide)

        header.addWidget(title); header.addStretch(); header.addWidget(self.balance); header.addWidget(close_btn)
        content.addLayout(header)
        
        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        # ФІКС: Вирівнювання сітки
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content.addWidget(self.grid_widget)
        
        self.refresh_shop()

    def refresh_shop(self):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w: w.deleteLater()
        self.balance.setText(f"💰 {int(self.engine.stats.data['money'])} (Lvl {self.engine.stats.data['level']})")
        for idx, (i_id, price) in enumerate(Settings.SHOP_PRICES.items()):
            self.grid.addWidget(ShopItem(i_id, price, self.engine.stats.data['level'], self.engine.buy_item), idx//4, idx%4)
        self.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()