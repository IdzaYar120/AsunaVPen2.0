from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from config.settings import Settings
import os
import logging

logger = logging.getLogger(__name__)

from core.resource_manager import ResourceManager

class TrayMenu(QSystemTrayIcon):
    def __init__(self, engine, app):
        super().__init__()
        self.engine = engine
        self.app = app
        
        # Завантажуємо іконку з пам'яті (перший кадр idle)
        frames = ResourceManager().get_frames("idle")
        if frames:
            self.setIcon(QIcon(frames[0]))
        else:
            logger.warning("Tray icon: 'idle' animation not found.")

        self.setContextMenu(self.create_menu())
        self.show()

    def create_menu(self):
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #2b2b2b; color: white; border: 1px solid #555; }")
        
        menu.addAction("🎒 Інвентар").triggered.connect(self.engine.open_inventory)
        menu.addAction("🛒 Магазин").triggered.connect(self.engine.open_shop)
        
        # Actions Submenu
        actions_menu = menu.addMenu("⚡ Дії")
        actions_menu.addAction("⚔️ Тренування").triggered.connect(self.engine.train)
        
        sleep_t = "☀️ Прокинутись" if self.engine.current_state == "sleep" else "🌙 Лягти спати"
        actions_menu.addAction(sleep_t).triggered.connect(self.engine.toggle_sleep)

        # Games Submenu
        games_menu = menu.addMenu("🎮 Міні-ігри")
        games_menu.addAction("💰 Полювання за монетами").triggered.connect(self.engine.open_minigame)
        games_menu.addAction("🎰 Ігрові автомати").triggered.connect(self.engine.open_slots)
        
        menu.addSeparator()
        menu.addAction("📝 Список справ").triggered.connect(self.engine.open_todo_list)
        menu.addSeparator()
        menu.addAction("❌ Вийти").triggered.connect(self.app.quit)
        return menu