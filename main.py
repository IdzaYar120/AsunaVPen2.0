import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.window import PetWindow
from ui.tray_menu import TrayMenu
from core.engine import PetEngine

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Створюємо вікно
    window = PetWindow()
    
    # Створюємо двигун
    engine = PetEngine(window)
    window.engine = engine
    
    # Трей
    tray = TrayMenu(engine, app)
    
    window.show()
    print("Програма запущена. Асуна має з'явитися на екрані!")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()