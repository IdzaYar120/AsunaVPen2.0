import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui.window import PetWindow
from ui.tray_menu import TrayMenu
from core.engine import PetEngine
from config.settings import Settings

def main():
    # НАЛАШТУВАННЯ ЛОГУВАННЯ
    log_file = Settings.SAVE_PATH.replace('stats.json', 'asuna.log')
    logging.basicConfig(
        level=Settings.LOG_LEVEL,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    window = PetWindow()
    engine = PetEngine(window)
    window.engine = engine
    tray = TrayMenu(engine, app)
    
    # Початкова позиція
    screen = app.primaryScreen().geometry()
    window.move(screen.width()-300, screen.height()-350)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()