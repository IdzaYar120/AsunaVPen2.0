from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QScrollArea, QGridLayout, QApplication)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QPixmap, QDrag, QPainter, QColor, QRadialGradient
import os
from config.settings import Settings

class IngredientIcon(QLabel):
    def __init__(self, item_id, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.setFixedSize(54, 54)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: rgba(255,255,255,10); border: 1px solid rgba(255,255,255,30); border-radius: 8px;")
        
        path = os.path.join(Settings.ICONS_DIR, f"{item_id}.png")
        if os.path.exists(path):
            self.setPixmap(QPixmap(path).scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.item_id)
            drag.setMimeData(mime)
            drag.setPixmap(self.grab())
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.MoveAction)

class RecipeCard(QFrame):
    fill_requested = pyqtSignal(list)
    def __init__(self, recipe_id, result_id, ingredients, unlocked=False, parent=None):
        super().__init__(parent)
        self.recipe_id = recipe_id
        self.ingredients = ingredients
        self.unlocked = unlocked
        self.expanded = False
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(180) # Reduced to fit better
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(4)
        
        # Header Section
        self.header = QWidget()
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(0,0,0,0)
        h_layout.setSpacing(8)
        
        icon = QLabel()
        path = os.path.join(Settings.ICONS_DIR, f"{result_id}.png")
        if os.path.exists(path):
            icon.setPixmap(QPixmap(path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        h_layout.addWidget(icon)
        
        name_map = {"burger": "Бургер", "sushi_set": "Суші-сет", "cake": "Торт", "salad": "Салат"}
        name = name_map.get(result_id, result_id.replace("_", " ").title())
        self.name_lbl = QLabel(name)
        self.name_lbl.setStyleSheet("color: white; font-weight: bold; border: none; font-size: 13px;")
        h_layout.addWidget(self.name_lbl)
        h_layout.addStretch()
        
        self.arrow = QLabel("▼" if unlocked else "🔒")
        self.arrow.setStyleSheet("color: rgba(255,215,0,150); border: none; font-size: 10px;")
        h_layout.addWidget(self.arrow)
        
        self.main_layout.addWidget(self.header)
        
        # Content Section
        self.content = QWidget()
        self.content.setVisible(False)
        c_vbox = QVBoxLayout(self.content)
        c_vbox.setContentsMargins(2, 5, 2, 2)
        c_vbox.setSpacing(8)
        
        # Ingredient Row
        ing_row = QHBoxLayout()
        ing_row.setSpacing(4)
        ing_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for ing in ingredients:
            ing_icon = QLabel()
            ing_path = os.path.join(Settings.ICONS_DIR, f"{ing}.png")
            if os.path.exists(ing_path):
                ing_icon.setPixmap(QPixmap(ing_path).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                ing_icon.setToolTip(ing.replace("_", " ").title())
                ing_icon.setStyleSheet("background: rgba(255,255,255,10); border-radius: 4px;")
            ing_row.addWidget(ing_icon)
        c_vbox.addLayout(ing_row)
        
        # Action Button
        self.fill_btn = QPushButton("ДОДАТИ")
        self.fill_btn.setFixedHeight(26)
        self.fill_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(255, 215, 0, 40); color: #FFD700; 
                border: 1px solid rgba(255, 215, 0, 100); border-radius: 6px; 
                font-weight: bold; font-size: 10px; 
            }
            QPushButton:hover { background: rgba(255, 215, 0, 80); color: white; }
        """)
        self.fill_btn.clicked.connect(lambda: self.fill_requested.emit(self.ingredients))
        c_vbox.addWidget(self.fill_btn)
        
        self.main_layout.addWidget(self.content)
        self.update_style()

    def update_style(self):
        if not self.unlocked:
            style = "background: rgba(30,30,30,120); border: 1px solid rgba(255,255,255,20); border-radius: 12px;"
            self.name_lbl.setStyleSheet("color: #666; font-weight: bold; border: none; font-size: 13px;")
        elif self.expanded:
            style = "background: rgba(255, 215, 0, 15); border: 2px solid rgba(255, 215, 0, 180); border-radius: 12px;"
        else:
            style = "background: rgba(255, 255, 255, 10); border: 1px solid rgba(255, 255, 255, 30); border-radius: 12px;"
        self.setStyleSheet(style)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.unlocked:
            self.expanded = not self.expanded
            self.content.setVisible(self.expanded)
            self.arrow.setText("▲" if self.expanded else "▼")
            self.update_style()

class CookingWindow(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.drag_pos = None # Initialize FIRST
        self.engine = engine
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(700, 450)
        
        self.ingredients_in_pot = []
        self.setup_ui()
        
    def setup_ui(self):
        if not self.layout():
            self.main_layout = QVBoxLayout(self)
            self.main_layout.setContentsMargins(0, 0, 0, 0) # Fill window exactly
        else:
            return self.refresh_recipes()
            
        # Container with Glassmorphism
        container = QFrame()
        container.setObjectName("container")
        container.setStyleSheet("""
            QFrame#container {
                background: rgba(20, 20, 20, 230);
                border: 2px solid rgba(255, 215, 0, 150);
                border-radius: 20px;
            }
        """)
        
        # Root layout for container (Header + Content)
        container_vbox = QVBoxLayout(container)
        container_vbox.setContentsMargins(0, 0, 0, 0)
        container_vbox.setSpacing(0)
        
        # --- TOP BAR (Close Button) ---
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 5, 10, 0)
        top_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { 
                background: transparent; color: rgba(255,255,255,100); 
                font-size: 18px; border: none; font-weight: bold;
            }
            QPushButton:hover { color: white; background: rgba(255,0,0,30); border-radius: 15px; }
        """)
        close_btn.clicked.connect(self.close)
        top_layout.addWidget(close_btn)
        container_vbox.addWidget(top_bar)
        
        # --- CONTENT AREA ---
        content_widget = QWidget()
        c_layout = QHBoxLayout(content_widget)
        c_layout.setContentsMargins(15, 0, 15, 15)
        c_layout.setSpacing(10)
        container_vbox.addWidget(content_widget)
        
        # --- LEFT: RECIPE BOOK ---
        left_panel = QVBoxLayout()
        title_l = QLabel("📖 КНИГА РЕЦЕПТІВ")
        title_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_l.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 13px; margin-bottom: 5px;")
        left_panel.addWidget(title_l)
        
        self.recipe_scroll = QScrollArea()
        self.recipe_scroll.setWidgetResizable(True)
        self.recipe_scroll.setStyleSheet("background: transparent; border: none;")
        self.recipe_container = QWidget()
        self.recipe_container.setStyleSheet("background: transparent;")
        self.recipe_vbox = QVBoxLayout(self.recipe_container)
        self.recipe_vbox.setContentsMargins(0, 5, 5, 5)
        self.recipe_vbox.setSpacing(10)
        
        self.refresh_recipes()
        
        self.recipe_scroll.setWidget(self.recipe_container)
        left_panel.addWidget(self.recipe_scroll)
        c_layout.addLayout(left_panel, 32)

        # --- CENTER: COOKING ZONE ---
        center_panel = QVBoxLayout()
        center_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_panel.setSpacing(10)
        
        pot_title = QLabel("🍳 ЗОНА ГОТУВАННЯ")
        pot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pot_title.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 14px;")
        center_panel.addWidget(pot_title)
        
        self.pot_area = QFrame()
        self.pot_area.setObjectName("pot")
        self.pot_area.setFixedSize(240, 240)
        self.pot_area.setAcceptDrops(True)
        self.pot_area.setStyleSheet("""
            QFrame#pot {
                background: rgba(255, 255, 255, 10);
                border: 2px dashed rgba(255, 215, 0, 80);
                border-radius: 120px;
            }
        """)
        
        self.pot_layout = QGridLayout(self.pot_area)
        self.pot_layout.setContentsMargins(30, 30, 30, 30)
        self.pot_layout.setSpacing(8)
        center_panel.addWidget(self.pot_area)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.cook_btn = QPushButton("🔥 ГОТУВАТИ")
        self.cook_btn.setFixedSize(130, 38)
        self.cook_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cook_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFD700, stop:1 #FFB900);
                color: black; font-weight: bold; font-size: 13px; border-radius: 10px;
            }
            QPushButton:hover { background: #FFC107; }
            QPushButton:disabled { background: rgba(80,80,80,100); color: #666; }
        """)
        self.cook_btn.clicked.connect(self.start_cooking)
        
        clear_btn = QPushButton("🗑️")
        clear_btn.setFixedSize(38, 38)
        clear_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,15); color: white; border-radius: 10px; border: 1px solid rgba(255,255,255,20); }
            QPushButton:hover { background: rgba(255,255,255,25); }
        """)
        clear_btn.clicked.connect(self.clear_pot)
        
        btn_row.addStretch()
        btn_row.addWidget(self.cook_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        
        center_panel.addLayout(btn_row)
        c_layout.addLayout(center_panel, 36)
        
        # --- RIGHT: INGREDIENTS ---
        right_panel = QVBoxLayout()
        title_r = QLabel("🥩 ІНГРЕДІЄНТИ")
        title_r.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_r.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 13px; margin-bottom: 5px;")
        right_panel.addWidget(title_r)
        
        self.ing_scroll = QScrollArea()
        self.ing_scroll.setWidgetResizable(True)
        self.ing_scroll.setStyleSheet("background: transparent; border: none;")
        self.ing_container = QWidget()
        self.ing_container.setStyleSheet("background: transparent;")
        self.ing_grid = QGridLayout(self.ing_container)
        self.ing_grid.setContentsMargins(5, 5, 5, 5)
        self.ing_grid.setSpacing(8)
        self.ing_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.ing_scroll.setWidget(self.ing_container)
        right_panel.addWidget(self.ing_scroll)
        c_layout.addLayout(right_panel, 32)
        
        self.main_layout.addWidget(container)
        self.refresh_inventory()
        self.refresh_inventory()

    def refresh_recipes(self):
        # Clear current recipes
        for i in reversed(range(self.recipe_vbox.count())): 
            item = self.recipe_vbox.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            
        unlocked = self.engine.stats.data.get("unlocked_recipes", [])
        
        # Recipes to show
        recipe_results = ["burger", "sushi_set", "cake", "salad"]
        
        for result_id in recipe_results:
            recipe_id = f"recipe_{result_id}"
            is_unlocked = recipe_id in unlocked
            
            # Find ingredients for this recipe in Settings
            ingredients = []
            for ing_set, res_id in Settings.COOKING_RECIPES.items():
                if res_id == result_id:
                    ingredients = list(ing_set)
                    break
                    
            card = RecipeCard(recipe_id, result_id, ingredients, unlocked=is_unlocked)
            card.fill_requested.connect(self.auto_fill_ingredients)
            self.recipe_vbox.addWidget(card)
            
        self.recipe_vbox.addStretch()

    def auto_fill_ingredients(self, ingredients_needed):
        if not ingredients_needed: return

        inventory = self.engine.stats.data.get("inventory", {})
        missing = []
        available_to_add = []
        
        # Simple count check (assumes 1 of each for now based on current recipe data)
        for ing in ingredients_needed:
            if inventory.get(ing, 0) > 0:
                available_to_add.append(ing)
            else:
                missing.append(ing)

        if missing:
            missing_names = [ing.replace("_", " ").title() for ing in missing]
            self.engine.window.create_floating_text(f"Бракує: {', '.join(missing_names)}", "#FF4444")
        
        self.clear_pot()
        for ing in available_to_add:
            self.add_to_pot(ing)
        
        if not missing:
            self.engine.window.create_floating_text("🛒 Інгредієнти додано!", "#4CAF50")

    def refresh_inventory(self):
        # Clear current grid
        for i in reversed(range(self.ing_grid.count())): 
            self.ing_grid.itemAt(i).widget().setParent(None)
            
        inventory = self.engine.stats.data.get("inventory", {})
        row, col = 0, 0
        for item_id in Settings.INGREDIENTS:
            count = inventory.get(item_id, 0)
            if count > 0:
                icon = IngredientIcon(item_id)
                count_lbl = QLabel(f"x{count}")
                count_lbl.setStyleSheet("color: rgba(255,255,255,150); font-size: 10px;")
                count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                widget = QWidget()
                w_layout = QVBoxLayout(widget)
                w_layout.setContentsMargins(2,2,2,2)
                w_layout.setSpacing(2)
                w_layout.addWidget(icon)
                w_layout.addWidget(count_lbl)
                
                self.ing_grid.addWidget(widget, row, col)
                col += 1
                if col > 2: col = 0; row += 1

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() in Settings.INGREDIENTS:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        pos = self.pot_area.mapFromGlobal(event.globalPosition().toPoint())
        if self.pot_area.rect().contains(pos):
            item_id = event.mimeData().text()
            self.add_to_pot(item_id)
            event.accept()

    def add_to_pot(self, item_id):
        if len(self.ingredients_in_pot) >= 9: return
        self.ingredients_in_pot.append(item_id)
        
        lbl = QLabel()
        path = os.path.join(Settings.ICONS_DIR, f"{item_id}.png")
        if os.path.exists(path):
            lbl.setPixmap(QPixmap(path).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
        
        idx = len(self.ingredients_in_pot) - 1
        self.pot_layout.addWidget(lbl, idx // 3, idx % 3)
        self.refresh_inventory()

    def clear_pot(self):
        self.ingredients_in_pot = []
        for i in reversed(range(self.pot_layout.count())):
            self.pot_layout.itemAt(i).widget().setParent(None)
        self.refresh_inventory()

    def start_cooking(self):
        if not self.ingredients_in_pot: return
        result = self.engine.cooking_manager.perform_cooking(self.ingredients_in_pot)
        if result:
            self.engine.window.create_floating_text(f"🍳 +{result}!", "#FFD700")
            if result == "burnt_food":
                self.engine.set_state("angry")
            else:
                self.engine.set_state("cooking")
        self.clear_pot()
        self.refresh_inventory()

    def on_recipe_click(self, recipe_id):
        # Expansion handled by RecipeCard
        pass

    def closeEvent(self, event):
        self.engine.close_cooking()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
