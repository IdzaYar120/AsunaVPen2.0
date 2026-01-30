from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QPixmap, QDrag
import os
from config.settings import Settings

class InventoryItem(QLabel):
    def __init__(self, item_id, count):
        super().__init__()
        self.item_id = item_id
        # Фіксований розмір слота
        self.setFixedSize(65, 65) 
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Завантаження іконки
        path = os.path.join(Settings.ICONS_DIR, f"{item_id}.png")
        if os.path.exists(path):
            self.setPixmap(QPixmap(path).scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        # СТИЛЬ СЛОТА
        self.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 10px;
            }
            QLabel:hover {
                background: rgba(255, 255, 255, 25);
                border: 1px solid #FFD700;
            }
        """)

        # ЦИФРА КІЛЬКОСТІ (Badge)
        self.count_label = QLabel(str(count), self)
        self.count_label.setFixedWidth(20)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("""
            background: rgba(0, 0, 0, 180);
            color: white;
            font-weight: bold;
            font-size: 10px;
            border-radius: 5px;
            border: none;
        """)
        # Позиціонуємо в правий нижній кут
        self.count_label.move(40, 42)

        # Підказка при наведенні
        item_type = "Солодощі (+Енергія)" if item_id in Settings.SWEET_STATS else "Їжа (+Голод)"
        if item_id in Settings.GIFT_STATS: item_type = "Подарунок (+Щастя)"
        elif item_id in Settings.PLAY_ITEMS: item_type = "Іграшка (Гра)"
        
        self.setToolTip(f"{item_id.replace('-', ' ').title()}\n{item_type}")

    def mouseMoveEvent(self, e):
        """Логіка Drag-and-Drop"""
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
        
        self.drag_pos = None
        
        # Контейнер
        self.container = QWidget(self)
        self.container.setStyleSheet("background: rgba(25, 25, 25, 240); border: 2px solid #666; border-radius: 15px;")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.container)
        
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(10, 10, 10, 10)

        # Шапка вікна
        header = QHBoxLayout()
        title = QLabel("ІНВЕНТАР")
        title.setStyleSheet("color: #AAA; font-weight: bold; font-size: 11px; border: none;")
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("background: rgba(255,255,255,20); color: white; border-radius: 10px; border: none; font-weight: bold;")
        close_btn.clicked.connect(self.hide)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        self.content_layout.addLayout(header)

        # Сітка предметів
        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setSpacing(8)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.content_layout.addWidget(self.grid_widget)

        self.refresh(stats)

    def refresh(self, stats):
        """Очищення та перемальовування сітки"""
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        items = stats.get("inventory", {})
        active_items = [(k, v) for k, v in items.items() if v > 0]
        
        for index, (item_id, count) in enumerate(active_items):
            row, col = index // 4, index % 4
            self.grid.addWidget(InventoryItem(item_id, count), row, col)
        
        self.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()