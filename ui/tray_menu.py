from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from config.settings import Settings
import os

class TrayMenu(QSystemTrayIcon):
    def __init__(self, engine, app):
        super().__init__()
        self.engine = engine
        self.app = app
        
        # Встановлюємо іконку для системного трею (біля годинника)
        # Беремо перший кадр анімації спокою
        icon_path = os.path.join(Settings.ANIM_DIR, "idle", "0.png")
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        
        # Підказка при наведенні мишки на іконку в треї
        level = self.engine.stats.data.get("level", 1)
        self.setToolTip(f"{Settings.PROJECT_NAME} (Рівень {level})")
        
        # Створюємо та встановлюємо контекстне меню
        self.setContextMenu(self.create_menu())
        self.show()

    def create_menu(self):
        """Створює меню, яке випадає при правому кліку на іконку в треї"""
        menu = QMenu()
        
        # Стилізація меню (темна тема)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
                font-family: Arial;
            }
            QMenu::item {
                padding: 5px 25px 5px 20px;
            }
            QMenu::item:selected {
                background-color: #4a4a4a;
            }
            QMenu::separator {
                height: 1px;
                background: #555;
                margin: 5px 10px;
            }
        """)

        # Кнопка 1: Відкрити інвентар (замість прямого годування)
        inv_btn = menu.addAction("🎒 Інвентар / Їжа")
        inv_btn.triggered.connect(self.engine.open_inventory)
        
        # Кнопка 2: Тренування
        train_btn = menu.addAction("⚔️ Тренування")
        train_btn.triggered.connect(self.engine.train)
        
        # Розділювач
        menu.addSeparator()
        
        # Кнопка 3: Вихід
        exit_btn = menu.addAction("❌ Вийти")
        exit_btn.triggered.connect(self.exit_game)
        
        return menu

    def exit_game(self):
        """Професійне завершення програми із збереженням усіх даних"""
        print("Збереження статистики та вихід...")
        self.engine.stats.save_stats()
        self.app.quit()