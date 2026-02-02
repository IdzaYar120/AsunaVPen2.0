from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QMimeData, QUrl, QSize
from PyQt6.QtGui import QDrag, QPixmap, QCursor, QAction
from config.settings import Settings
import os

class GardenPot(QWidget):
    def __init__(self, index, manager, parent_window):
        super().__init__()
        self.index = index
        self.manager = manager
        self.parent_window = parent_window
        
        self.setFixedSize(120, 220) # Increased height for tall plants
        self.setAcceptDrops(True)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        
        # Container for Layering
        self.container = QWidget(self)
        self.container.setFixedSize(120, 180) # Area for Pot + Plant
        
        # Pot Image (Bottom Aligned)
        self.pot_img = QLabel(self.container)
        self.pot_img.setFixedSize(100, 100)
        self.pot_img.move(10, 80) # Bottom of container
        self.load_pot_image()
        
        # Plant Image (Overlay - Anchored at Bottom of Pot)
        self.plant_img = QLabel(self.container)
        self.plant_img.setFixedSize(100, 150) # Width of pot, taller height
        self.plant_img.move(10, 30) # Overlap pot, extending upwards
        self.plant_img.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        
        # Withered Overlay
        self.withered_img = QLabel(self.container)
        self.withered_img.setFixedSize(100, 100)
        self.withered_img.move(10, 80) # Matches pot position
        self.withered_img.setVisible(False)
        self.withered_img.setStyleSheet("background: rgba(0,0,0,100); border-radius: 50%;") 
        
        self.layout.addWidget(self.container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Water Bar
        self.water_bar = QProgressBar()
        self.water_bar.setFixedSize(80, 10)
        self.water_bar.setTextVisible(False)
        self.water_bar.setRange(0, 1000) # Higher precision
        self.water_bar.setValue(0)
        
        self.layout.addWidget(self.water_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def load_pot_image(self):
        path = os.path.join(Settings.BASE_DIR, "assets", "ui", "garden", "pot.png")
        if os.path.exists(path):
            pix = QPixmap(path)
            self.pot_img.setPixmap(pix.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.pot_img.setStyleSheet("background: #8B4513; border-radius: 10px;")
            self.pot_img.setText("POT")

    def update_state(self):
        data = self.manager.get_pot(self.index)
        if not data: return
        
        # Water Bar
        w = data["water"]
        self.water_bar.setValue(int(w * 10)) # Map 0-100 to 0-1000
        
        if w > 50: col = "#00BFFF"
        elif w > 20: col = "#FFD700"
        else: col = "#FF4444"
        
        # Simplified style to avoid radius rendering issues at low widths
        self.water_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #555;
                border-radius: 5px;
                background: #333;
            }}
            QProgressBar::chunk {{
                background-color: {col};
                border-radius: 3px; /* Reduced radius */
            }}
        """)
        
        # Plant
        plant = data["plant"]
        stage = data["stage"]
        
        if plant:
            # Construct path: assets/ui/garden/plants/{plant}_{stage}.png
            # Or just {plant}_{stage}.png if in same folder
            p_path = os.path.join(Settings.BASE_DIR, "assets", "ui", "garden", "plants", f"{plant}_{stage}.png")
            
            if os.path.exists(p_path):
                pix = QPixmap(p_path)
                # SCALE TO POT WIDTH (100) and RELATIVE HEIGHT (up to 150)
                self.plant_img.setPixmap(pix.scaled(100, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.plant_img.show()
            else:
                self.plant_img.setText(f"{plant}\nLvl {stage}")
                self.plant_img.setStyleSheet("color: lime; font-weight: bold;")
                self.plant_img.show()
                
            # Withered check
            if w <= 0:
                self.plant_img.hide()
                self.pot_img.hide() # Hide base pot as withered image includes it
                self.withered_img.setVisible(True)
                w_path = os.path.join(Settings.BASE_DIR, "assets", "ui", "garden", "plant_withered.png")
                if os.path.exists(w_path):
                     # Match plant_img geometry
                    self.withered_img.setFixedSize(100, 150)
                    self.withered_img.move(10, 30)
                    self.withered_img.setPixmap(QPixmap(w_path).scaled(100, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    self.withered_img.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
            else:
                self.pot_img.show() # Ensure pot is visible for healthy plants
                self.withered_img.setVisible(False)
                
        else:
            self.plant_img.hide()
            self.withered_img.hide()
            self.water_bar.setValue(0)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Harvest check
            data = self.manager.get_pot(self.index)
            if data and data["plant"] and data["stage"] == 4 and data["water"] > 0:
                item = self.manager.harvest(self.index)
                if item:
                    self.parent_window.engine.window.create_floating_text(f"+1 {item}", "#00FF00")
                    self.parent_window.refresh()
            elif data and data["water"] <= 0:
                 # Withered click - clear it?
                 self.manager.harvest(self.index) # Handles clearing
                 self.parent_window.refresh()
                 
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            txt = event.mimeData().text()
            if txt == "watering_can" or txt.startswith("seed_"):
                event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        txt = event.mimeData().text()
        
        if txt == "watering_can":
            if self.manager.water_pot(self.index):
                self.parent_window.engine.sound.play("water") # Need to add sound? Or existing
                self.update_state()
            event.accept()
            
        elif txt.startswith("seed_"):
            if self.manager.plant_seed(self.index, txt):
                self.parent_window.engine.sound.play("plant") # Placeholder
                self.update_state()
                # Remove seed from inventory
                inv = self.parent_window.engine.stats.data["inventory"]
                if inv.get(txt, 0) > 0:
                    inv[txt] -= 1
                    if inv[txt] <= 0: del inv[txt]
                    self.parent_window.engine.stats.save_stats()
                    self.parent_window.refresh_inventory()
            event.accept()

class GardenWindow(QWidget):
    def __init__(self, engine, manager):
        super().__init__()
        self.engine = engine
        self.manager = manager
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        # Container (Brown Table Background)
        self.container = QFrame()
        self.container.setFixedSize(550, 350) # Increased to 350
        self.container.setStyleSheet("""
            QFrame {
                background-color: #5D4037; /* Brown */
                border: 2px solid #3E2723;
                border-radius: 15px;
            }
        """)
        layout.addWidget(self.container)
        
        # Grid for Pots
        pot_layout = QHBoxLayout(self.container)
        pot_layout.setSpacing(20)
        pot_layout.setContentsMargins(20, 20, 20, 80) # Bottom margin for inventory bar
        
        self.pots = []
        for i in range(4):
            pot = GardenPot(i, self.manager, self)
            pot_layout.addWidget(pot)
            self.pots.append(pot)
            
        # Inventory Bar (Overlay at bottom)
        self.inv_bar = QFrame(self.container)
        self.inv_bar.setFixedSize(510, 60)
        self.inv_bar.move(20, 280) # Moved down to 280
        self.inv_bar.setStyleSheet("background: rgba(0,0,0,150); border-radius: 10px;")
        
        self.inv_layout = QHBoxLayout(self.inv_bar)
        self.inv_layout.setContentsMargins(5, 5, 5, 5)
        self.inv_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Close Button
        close_btn = QLabel("✕", self.container)
        close_btn.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        close_btn.move(520, 10)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.mousePressEvent = lambda e: self.hide()
        
        # Timer for updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_growth)
        self.timer.start(1000) # Check every second
        
        self.drag_pos = None

    def refresh(self):
        for pot in self.pots:
            pot.update_state()
        self.refresh_inventory()

    def refresh_inventory(self):
        # Clear existing items
        while self.inv_layout.count():
            child = self.inv_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        items = self.engine.stats.data.get("inventory", {})
        
        # Add Watering Can (if owned)
        if items.get("watering_can", 0) > 0:
            self.add_inv_item("watering_can", 1)
            
        # Add Seeds
        for item, count in items.items():
            if item.startswith("seed_") and count > 0:
                self.add_inv_item(item, count)

    def add_inv_item(self, item_id, count):
        lbl = QLabel()
        lbl.setFixedSize(48, 48)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Resolve Path
        path = Settings.get_icon_path(item_id)
        if os.path.exists(path):
            lbl.setPixmap(QPixmap(path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl.setText(item_id[:2])
            
        lbl.setToolTip(f"{item_id} (x{count})")
        lbl.setStyleSheet("border: 1px solid #555; border-radius: 5px; background: rgba(255,255,255,20);")
        
        # Drag Logic
        def start_drag(e):
            drag = QDrag(lbl)
            mime = QMimeData()
            mime.setText(item_id)
            drag.setMimeData(mime)
            drag.setPixmap(lbl.pixmap())
            drag.setHotSpot(e.pos())
            drag.exec(Qt.DropAction.CopyAction)
            
        lbl.mousePressEvent = start_drag
        self.inv_layout.addWidget(lbl)

    def update_growth(self):
        # Trigger manager update
        self.manager.update_growth()
        # Refresh UI
        for pot in self.pots:
            pot.update_state()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
