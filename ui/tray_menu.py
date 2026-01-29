from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from config.settings import Settings
import os
import logging

logger = logging.getLogger(__name__)

class TrayMenu(QSystemTrayIcon):
    def __init__(self, engine, app):
        super().__init__()
        self.engine = engine
        self.app = app
        
        # ФІКС: Надійна перевірка іконки
        icon_path = os.path.join(Settings.ANIM_DIR, "idle", "0.png")
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            logger.warning(f"Tray icon not found at {icon_path}. Using fallback.")

        self.setContextMenu(self.create_menu())
        self.show()

    def create_menu(self):
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #2b2b2b; color: white; border: 1px solid #555; }")
        menu.addAction("🎒 Інвентар").triggered.connect(self.engine.open_inventory)
        menu.addAction("🛒 Магазин").triggered.connect(self.engine.open_shop)
        menu.addAction("⚔️ Тренування").triggered.connect(self.engine.train)
        menu.addSeparator()
        menu.addAction("❌ Вийти").triggered.connect(self.app.quit)
        return menu