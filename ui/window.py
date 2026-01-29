from PyQt6.QtWidgets import QWidget, QLabel, QProgressBar, QVBoxLayout, QMenu, QApplication, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtGui import QPixmap
import os, time
from config.settings import Settings

class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        self.header_spacing = 80 
        
        self.label = QLabel(self)
        self.emote_label = QLabel(self)
        self.emote_label.setFixedSize(60, 60)
        self.emote_label.hide()
        
        # XP BAR (тепер прихований за замовчуванням)
        self.bar_xp = QProgressBar(self)
        self.bar_xp.setFixedHeight(4)
        self.bar_xp.setTextVisible(False)
        self.bar_xp.setStyleSheet("QProgressBar { border: none; background: rgba(0,0,0,80); } QProgressBar::chunk { background: #FFD700; }")
        self.bar_xp.hide()

        # Панель показників
        self.stats_panel = QWidget(self)
        self.stats_panel.setFixedWidth(130)
        self.stats_panel.setFixedHeight(45)
        self.stats_panel.hide()
        layout = QVBoxLayout(self.stats_panel)
        layout.setSpacing(2); layout.setContentsMargins(5, 5, 5, 5)

        self.bar_hunger = self.create_bar("#FF4444")
        self.bar_energy = self.create_bar("#44FF44")
        self.bar_health = self.create_bar("#4444FF")
        for b in [self.bar_hunger, self.bar_energy, self.bar_health]: layout.addWidget(b)

        self.is_dragging, self.drag_pos, self.press_pos = False, QPoint(), QPoint()

        # Таймер для приховування XP бару
        self.xp_hide_timer = QTimer()
        self.xp_hide_timer.setSingleShot(True)
        self.xp_hide_timer.timeout.connect(self.bar_xp.hide)

    def create_bar(self, color):
        bar = QProgressBar()
        bar.setFixedHeight(5); bar.setRange(0, 100); bar.setTextVisible(False)
        bar.setStyleSheet(f"QProgressBar {{ border-radius: 2px; background: rgba(0,0,0,150); }} QProgressBar::chunk {{ background: {color}; }}")
        return bar

    def update_stats_ui(self, h, e, hl):
        self.bar_hunger.setValue(int(h))
        self.bar_energy.setValue(int(e))
        self.bar_health.setValue(int(hl))

    def update_xp_ui(self, xp, lvl, force_show=False):
        self.bar_xp.setRange(0, Settings.LEVEL_UP_XP)
        self.bar_xp.setValue(int(xp))
        self.bar_xp.setToolTip(f"Рівень {lvl} | XP: {int(xp)}/{Settings.LEVEL_UP_XP}")
        if force_show:
            self.bar_xp.show()
            self.xp_hide_timer.start(5000) # Показувати 5 сек

    def create_floating_text(self, text, color="#FFD700"):
        label = QLabel(text, self); label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 18px;")
        label.adjustSize(); x = (self.width() - label.width()) // 2; y = self.header_spacing + 10
        label.move(x, y); label.show()
        
        move_anim = QPropertyAnimation(label, b"pos"); move_anim.setDuration(1500)
        move_anim.setStartValue(QPoint(x, y)); move_anim.setEndValue(QPoint(x, y - 70))
        
        eff = QGraphicsOpacityEffect(label); label.setGraphicsEffect(eff)
        fade = QPropertyAnimation(eff, b"opacity"); fade.setDuration(1500)
        fade.setStartValue(1.0); fade.setEndValue(0.0)

        group = QParallelAnimationGroup(self)
        group.addAnimation(move_anim); group.addAnimation(fade)
        group.finished.connect(label.deleteLater); group.start()

    def render_pet(self, px):
        if self.size() != (px.width(), px.height() + self.header_spacing):
            self.setFixedSize(px.width(), px.height() + self.header_spacing)
            self.label.setGeometry(0, self.header_spacing, px.width(), px.height())
        self.label.setPixmap(px); self.bar_xp.setGeometry(0, 0, self.width(), 4)
        self.emote_label.move((self.width() - 60) // 2, 10)
        self.bar_xp.raise_(); self.emote_label.raise_(); self.stats_panel.raise_(); self.show()

    def enterEvent(self, e):
        self.stats_panel.move((self.width()-130)//2, self.height()-48)
        self.stats_panel.show(); self.bar_xp.show()

    def leaveEvent(self, e):
        self.stats_panel.hide(); self.xp_hide_timer.start(2000)

    def show_emote(self, name):
        path = os.path.join(Settings.UI_DIR, f"{name}.png")
        if os.path.exists(path):
            self.emote_label.setPixmap(QPixmap(path).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
            self.emote_label.show(); QTimer.singleShot(3000, self.emote_label.hide)

    def contextMenuEvent(self, event):
        if self.engine:
            menu = QMenu(self)
            menu.addAction("🎒 Інвентар").triggered.connect(self.engine.open_inventory)
            menu.addAction("⚔️ Тренування").triggered.connect(self.engine.train)
            
            # НОВА КНОПКА СНУ
            sleep_text = "☀️ Прокинутись" if self.engine.current_state == "sleep" else "🌙 Лягти спати"
            menu.addAction(sleep_text).triggered.connect(self.engine.toggle_sleep)
            
            menu.addSeparator()
            menu.addAction("❌ Вийти").triggered.connect(QApplication.quit)
            menu.exec(event.globalPos())

    def dragEnterEvent(self, e): e.accept() if e.mimeData().hasText() else e.ignore()
    def dropEvent(self, e):
        if self.engine: self.engine.use_item_from_inventory(e.mimeData().text())

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.is_dragging, self.press_pos = True, e.globalPosition().toPoint()
            self.drag_pos = self.press_pos - self.frameGeometry().topLeft()
            if self.engine: self.engine.handle_drag_start()

    def mouseMoveEvent(self, e):
        if self.is_dragging: self.move(e.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            if self.engine:
                if (e.globalPosition().toPoint() - self.press_pos).manhattanLength() < 5:
                    self.engine.handle_click()
                else: self.engine.release_emotion()