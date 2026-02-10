from PyQt6.QtWidgets import QApplication
import logging

logger = logging.getLogger(__name__)

class WindowManager:
    """
    Manages all sub-windows and UI components for the Pet Engine.
    Decouples UI management from the core logic.
    """
    def __init__(self, engine):
        self.engine = engine
        
        # Window References
        self.shop_win = None
        self.inventory_win = None
        self.settings_win = None
        self.music_win = None
        self.music_widget = None
        self.todo_win = None
        self.ach_win = None
        self.cooking_win = None
        self.slots_win = None
        self.minigame_win = None
        self.garden_win = None
        self.journal_win = None
        self.mail_win = None
        
    def close_all(self):
        """Closes all active windows."""
        if self.shop_win: self.shop_win.close()
        if self.inventory_win: self.inventory_win.close()
        if self.settings_win: self.settings_win.close()
        if self.music_win: self.music_win.close()
        if self.music_widget: self.music_widget.close()
        if self.todo_win: self.todo_win.close()
        if self.ach_win: self.ach_win.close()
        if self.cooking_win: self.cooking_win.close()
        if self.slots_win: self.slots_win.close()
        if self.minigame_win: self.minigame_win.close()
        if self.garden_win: self.garden_win.close()
        if self.journal_win: self.journal_win.close()
        if self.mail_win: self.mail_win.close()

    def _center_window(self, win, x_offset=0, y_offset=0):
        """Helper to position window relative to the pet."""
        if win and not win.isHidden():
            win.move(self.engine.window.x() + x_offset, self.engine.window.y() + y_offset)
            win.show()
            win.raise_()

    # --- Specific Window Openers ---

    def open_shop(self):
        from ui.shop import ShopWindow
        if not self.shop_win:
            self.shop_win = ShopWindow(self.engine)
            
        if self.shop_win.isHidden():
            self.shop_win.refresh_shop()
            # Smart positioning
            screen = QApplication.primaryScreen().availableGeometry()
            main_w = self.engine.window
            
            # Default to left of pet, clamp to screen
            nx = max(screen.left() + 10, min(main_w.x() - 100, screen.right() - self.shop_win.width() - 10))
            ny = max(screen.top() + 10, min(main_w.y(), screen.bottom() - self.shop_win.height() - 10))
            
            self.shop_win.move(int(nx), int(ny))
            self.shop_win.show()
        else:
            self.shop_win.hide()

    def open_inventory(self):
        from ui.inventory import InventoryWindow
        if not self.inventory_win:
            self.inventory_win = InventoryWindow(self.engine)
            
        self.inventory_win.refresh()
        self.engine.window.position_window(self.inventory_win)
        self.inventory_win.show()
        self.inventory_win.raise_()
        
    def open_settings(self):
        from ui.settings_window import SettingsWindow
        if not self.settings_win:
            self.settings_win = SettingsWindow(self.engine)
            
        # Center relative to pet, slightly offset
        self.settings_win.move(self.engine.window.x() - 100, self.engine.window.y())
        self.settings_win.show()
        self.settings_win.raise_()

    def open_todo_list(self):
        from ui.todo_list import TodoWindow
        if not self.todo_win:
            self.todo_win = TodoWindow(self.engine.task_manager, self.engine)
            
        if self.todo_win.isHidden():
            self.todo_win.refresh_list()
            self.todo_win.move(self.engine.window.x() + self.engine.window.width() + 20, self.engine.window.y())
            self.todo_win.show()
        else:
            self.todo_win.hide()

    def open_achievements(self):
        from ui.achievements import AchievementWindow
        if not self.ach_win:
            self.ach_win = AchievementWindow(self.engine.stats.data)
        
        self.ach_win.refresh(self.engine.stats.data)
        self.engine.window.position_window(self.ach_win)
        self.ach_win.show()

    def open_cooking(self):
        from ui.cooking_window import CookingWindow
        if not self.cooking_win:
            self.cooking_win = CookingWindow(self.engine)
            
        self.engine.res.load_animation("cooking")
        self.engine.window.position_window(self.cooking_win)
        self.cooking_win.refresh_inventory()
        self.cooking_win.show()
        self.cooking_win.raise_()
        
        self.engine.set_state("cooking")
        self.engine.window.show_emote("cooking")

    def close_cooking(self):
        if self.cooking_win:
            self.cooking_win.hide()
            self.engine.set_state("idle")
            self.engine.res.unload_animation("cooking")

    # --- Games ---

    def open_slots(self):
        from ui.slots import SlotsWindow
        if not self.slots_win or not self.slots_win.isVisible():
            self.slots_win = SlotsWindow(self.engine)
            self.slots_win.move(self.engine.window.x(), self.engine.window.y() - 320)
            self.slots_win.show()

    def open_minigame(self):
        from ui.minigame import CoinGameWindow
        if not self.minigame_win or not self.minigame_win.isVisible():
            self.minigame_win = CoinGameWindow(self.engine)
            self.minigame_win.move(self.engine.window.x(), self.engine.window.y() - 320)
            self.minigame_win.show()

    def open_garden(self):
        from ui.garden_window import GardenWindow
        if not self.garden_win:
            self.garden_win = GardenWindow(self.engine, self.engine.garden_manager)
            
        if self.garden_win.isHidden():
            self.garden_win.move(self.engine.window.x() - 50, self.engine.window.y() + 300)
            self.garden_win.refresh()
            self.garden_win.show()
        else:
            self.garden_win.hide()

    def open_journal(self):
        from ui.journal_window import JournalWindow
        if not self.journal_win:
            self.journal_win = JournalWindow(self.engine.journal)
        
        self.journal_win.refresh()
        self.engine.window.position_window(self.journal_win)
        self.journal_win.show()
        self.journal_win.raise_()

    def show_mail(self, mail_data):
        from ui.mail_window import MailWindow
        # Mail is usually a one-off popup
        self.mail_win = MailWindow(self.engine, mail_data)
        self.engine.window.position_window(self.mail_win)
        self.mail_win.show()
        self.mail_win.raise_()

    # --- Music ---

    def open_music_player(self):
        # Hide widget if active
        if self.music_widget: self.music_widget.hide()
        
        from ui.music_window import MusicWindow
        if not self.music_win:
            self.music_win = MusicWindow(self.engine)
            
        self.engine.window.position_window(self.music_win)
        self.music_win.show()
        self.music_win.raise_()

    def dock_music_player(self):
        """Switch Main Player -> Mini Widget."""
        if self.music_win: self.music_win.hide()
        
        if self.engine.music_player.playlist:
            from ui.music_widget import MusicWidget
            if not self.music_widget:
                self.music_widget = MusicWidget(self.engine.music_player, self.engine.window)
            
            self.update_music_widget_pos()
            self.music_widget.show()
            self.music_widget.raise_()

    def update_music_widget_pos(self):
        if self.music_widget and self.music_widget.isVisible():
            self.music_widget.update_position(
                self.engine.window.x(), self.engine.window.y(),
                self.engine.window.width(), self.engine.window.height()
            )
