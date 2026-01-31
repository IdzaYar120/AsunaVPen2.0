from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout, QPushButton, QHBoxLayout, QTabWidget, QScrollArea, QFrame
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QImage
import os
from config.settings import Settings

class ShopItem(QWidget):
    def __init__(self, item_id, price, level, money, on_buy_callback):
        super().__init__()
        self.setFixedSize(90, 130) # Increased height for larger icons
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)
        
        # Determine Color Border based on rarity/type
        border_col = "#555"
        if item_id in Settings.GIFT_STATS: border_col = "#FF69B4" # Pink for gifts
        elif item_id in Settings.HEALTH_FOOD_STATS: border_col = "#4CAF50" # Green for health
        
        container = QFrame()
        container.setObjectName("itemContainer")
        container.setStyleSheet(f"""
            QFrame#itemContainer {{
                background: rgba(40, 40, 40, 200);
                border: 1px solid {border_col};
                border-radius: 8px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Check lock
        req_level = Settings.SHOP_UNLOCKS.get(item_id, 1)
        is_locked = level < req_level
        can_afford = money >= price
        
        # Icon
        path = os.path.join(Settings.ICONS_DIR, f"{item_id}.png")
        icon = QLabel()
        icon.setFixedSize(60, 60) # Larger icon area
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if os.path.exists(path):
            pix = QPixmap(path).scaled(55, 55, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            if is_locked:
                img = pix.toImage(); img.convertTo(QImage.Format.Format_Grayscale8); pix = QPixmap.fromImage(img)
                pix.setDevicePixelRatio(2.0)
            icon.setPixmap(pix)
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Name & Price
        name = item_id.replace('-', ' ').title()
        if len(name) > 10: name = name[:8] + ".." 
        
        info_text = f"{name}\n💰 {price}"
        if is_locked: info_text = f"Lvl {req_level}\n🔒"
        
        info = QLabel(info_text)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet(f"color: {'#888' if is_locked else 'white'}; font-size: 9px; font-weight: bold;")
        layout.addWidget(info)
        
        # Button
        btn = QPushButton("Купити")
        btn.setFixedHeight(18)
        if is_locked:
            btn.setText(f"Lvl {req_level}")
            btn.setEnabled(False)
            btn.setStyleSheet("background: #444; color: #888; border-radius: 4px; border:none; font-size: 9px;")
        else:
            if can_afford:
                btn.setStyleSheet("background: #2E7D32; color: white; border-radius: 4px; border:none; font-size: 10px; font-weight: bold;")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                btn.setStyleSheet("background: #C62828; color: #DDD; border-radius: 4px; border:none; font-size: 10px; font-weight: bold;")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                
            btn.clicked.connect(lambda: on_buy_callback(item_id, price))
            
        layout.addWidget(btn)
        main_layout.addWidget(container)

class ShopWindow(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.drag_pos = None
        
        # Main Container
        self.container = QWidget(self)
        self.container.setFixedSize(450, 350) # Increased width
        self.setFixedSize(450, 350)
        self.container.setStyleSheet("""
            QWidget { background: #1E1E24; border: 1px solid #FFD700; border-radius: 10px; color: white; }
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #333; color: #AAA; padding: 6px 10px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { background: #FFD700; color: #000; font-weight: bold; }
            QTabBar::tab:hover { background: #555; }
        """)
        
        layout = QVBoxLayout(self.container)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("🛒 МАГАЗИН")
        title.setStyleSheet("font-size: 14px; font-weight: bold; border:none; color: #FFD700;")
        
        self.balance = QLabel()
        self.balance.setStyleSheet("font-size: 12px; font-weight: bold; color: #4CAF50; border:none;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("background: transparent; color: #AAA; font-size: 16px; border:none;")
        close_btn.clicked.connect(self.hide)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.balance)
        header.addWidget(close_btn)
        layout.addLayout(header)
        
        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.refresh_shop()

    def refresh_shop(self):
        # Save current tab index
        current_idx = self.tabs.currentIndex()
        if current_idx < 0: current_idx = 0
        
        self.tabs.clear()
        self.balance.setText(f"💰 {int(self.engine.stats.data['money'])}")
        
        categories = {
            "🍔 Їжа": [],
            "🍭 Солодощі": [],
            "🥩 Інгредієнти": [],
            "📜 Рецепти": [],
            "🍎 Здоров'я": [],
            "🎁 Подарунки": []
        }
        
        # Categorize
        for item, price in Settings.SHOP_PRICES.items():
            if item in Settings.INGREDIENTS: categories["🥩 Інгредієнти"].append((item, price))
            elif item.startswith("recipe_"): categories["📜 Рецепти"].append((item, price))
            elif item in Settings.FOOD_STATS: categories["🍔 Їжа"].append((item, price))
            elif item in Settings.SWEET_STATS: categories["🍭 Солодощі"].append((item, price))
            elif item in Settings.HEALTH_FOOD_STATS: categories["🍎 Здоров'я"].append((item, price))
            else: categories["🎁 Подарунки"].append((item, price))
            
        # Create Tabs
        for cat_name, items in categories.items():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical { width: 8px; background: #222; } QScrollBar::handle:vertical { background: #555; border-radius: 4px; }")
            
            page = QWidget()
            page.setStyleSheet("background: transparent; border: none;") # Transparent inside scroll
            grid = QGridLayout(page)
            grid.setSpacing(10)
            grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            
            for i, (item_id, price) in enumerate(items):
                item_widget = ShopItem(item_id, price, self.engine.stats.data['level'], self.engine.stats.data['money'], self.engine.buy_item)
                grid.addWidget(item_widget, i // 4, i % 4) # 4 columns
                
            scroll.setWidget(page)
            self.tabs.addTab(scroll, cat_name)
            
        # Restore tab index
        if current_idx < self.tabs.count():
            self.tabs.setCurrentIndex(current_idx)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()