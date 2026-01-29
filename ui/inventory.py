from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QPixmap, QDrag
import os
from config.settings import Settings

class InventoryItem(QLabel):
    def __init__(self, item_id, count):
        super().__init__()
        self.item_id = item_id
        
        # Використовуємо Settings.ICONS_DIR
        path = os.path.join(Settings.ICONS_DIR, f"{item_id}.png")
        
        if os.path.exists(path):
            self.setPixmap(QPixmap(path).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            print(f"Помилка: Іконка не знайдена: {path}")

        item_type = "Солодощі (+Енергія)" if item_id in Settings.SWEET_STATS else "Їжа (+Голод)"
        self.setToolTip(f"{item_id.replace('-', ' ').title()}\n{item_type}\nКількість: {count}")
        self.setStyleSheet("background: rgba(255,255,255,15); border-radius: 5px; padding: 2px;")

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.item_id)
            drag.setMimeData(mime)
            drag.setPixmap(self.pixmap())
            drag.exec(Qt.DropAction.MoveAction)

class InventoryWindow(QWidget):
    def __init__(self, stats):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.container = QWidget(self)
        self.container.setStyleSheet("background: rgba(25, 25, 25, 230); border: 2px solid #666; border-radius: 12px;")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.container)
        
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(10)
        self.grid.setContentsMargins(15, 15, 15, 15)

    def refresh(self, stats):
        # Очищення
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w: w.deleteLater()
            
        items = stats.get("inventory", {})
        active_items = [(k, v) for k, v in items.items() if v > 0]
        
        # Сітка 4 стовпці
        for index, (item_id, count) in enumerate(active_items):
            row = index // 4
            col = index % 4
            self.grid.addWidget(InventoryItem(item_id, count), row, col)
        
        self.adjustSize()