from PyQt6.QtWidgets import QWidget, QLabel, QProgressBar, QVBoxLayout, QMenu, QApplication, QGraphicsOpacityEffect, QInputDialog, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QCoreApplication, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QIntValidator
import os, time
from config.settings import Settings

class HappinessGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedSize(50, 50); self.value = 100.0
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#4CAF50") if self.value > 60 else QColor("#FFEB3B") if self.value > 25 else QColor("#F44336")
        p.setPen(QPen(QColor(50, 50, 50, 100), 4)); p.drawEllipse(5, 5, 40, 40)
        p.setPen(QPen(color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(QRectF(5, 5, 40, 40), 90 * 16, int(-(self.value/100)*360*16))
        p.setPen(QColor("white")); p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{int(self.value)}")

class ModernInputDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.container = QWidget(self)
        self.container.setStyleSheet("background: rgba(30,30,30,240); border: 2px solid #FFD700; border-radius: 15px; color: white;")
        layout = QVBoxLayout(self); layout.addWidget(self.container); v_layout = QVBoxLayout(self.container)
        title = QLabel("ЧАС НАВЧАННЯ (хв)"); title.setStyleSheet("border:none; font-weight:bold; color:#FFD700;")
        self.input = QLineEdit(); self.input.setValidator(QIntValidator(1, 180)); self.input.setText("25")
        self.input.setStyleSheet("background: rgba(255,255,255,20); border: 1px solid #555; border-radius: 8px; padding: 5px;")
        btn_l = QHBoxLayout(); ok = QPushButton("СТАРТ"); cancel = QPushButton("СКАСУВАТИ")
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        btn_l.addWidget(cancel); btn_l.addWidget(ok); v_layout.addWidget(title); v_layout.addWidget(self.input); v_layout.addLayout(btn_l)
        self.result = None; self.setFixedSize(200, 130)
    def accept(self): self.result = int(self.input.text()); self.hide()
    def reject(self): self.result = None; self.hide()

class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setAcceptDrops(True)
        self.header_spacing = int(80 * Settings.SCALE_FACTOR)
        self.label = QLabel(self); self.emote_label = QLabel(self); self.emote_label.setFixedSize(60, 60); self.emote_label.hide()
        self.happiness_gauge = HappinessGauge(self); self.happiness_gauge.hide()
        self.timer_label = QLabel(self); self.timer_label.setFixedWidth(70); self.timer_label.hide()
        self.timer_label.setStyleSheet("background: rgba(0,0,0,160); color: #00FF00; font-weight: bold; border-radius: 8px;")
        self.bar_xp = QProgressBar(self); self.bar_xp.setFixedHeight(4); self.bar_xp.hide()
        self.bar_xp.setStyleSheet("QProgressBar { border: none; background: rgba(0,0,0,80); } QProgressBar::chunk { background: #FFD700; }")
        self.stats_panel = QWidget(self); self.stats_panel.setFixedWidth(int(130*Settings.SCALE_FACTOR+50)); self.stats_panel.setFixedHeight(55); self.stats_panel.hide()
        layout = QVBoxLayout(self.stats_panel); self.bar_hunger = self.create_bar("#FF4444"); self.bar_energy = self.create_bar("#44FF44"); self.bar_health = self.create_bar("#4444FF")
        for b in [self.bar_hunger, self.bar_energy, self.bar_health]: layout.addWidget(b)
        self.is_dragging, self.drag_pos, self.press_pos = False, QPoint(), QPoint()
        self.xp_hide_timer = QTimer(); self.xp_hide_timer.setSingleShot(True); self.xp_hide_timer.timeout.connect(self.bar_xp.hide)
        self.custom_input = None

    def create_bar(self, color):
        bar = QProgressBar(); bar.setFixedHeight(5); bar.setRange(0, 100); bar.setTextVisible(False)
        bar.setStyleSheet(f"QProgressBar {{ border-radius: 2px; background: rgba(0,0,0,150); }} QProgressBar::chunk {{ background: {color}; }}")
        return bar

    def update_stats_ui(self, h, e, hl, hap):
        self.bar_hunger.setValue(int(h)); self.bar_energy.setValue(int(e)); self.bar_health.setValue(int(hl))
        self.happiness_gauge.value = hap; self.happiness_gauge.update()

    def update_xp_ui(self, xp, lvl, force_show=False):
        self.bar_xp.setRange(0, Settings.LEVEL_UP_XP); self.bar_xp.setValue(int(xp))
        if force_show: self.bar_xp.show(); self.xp_hide_timer.start(5000)

    def render_pet(self, px):
        nw, nh = px.width(), px.height() + self.header_spacing
        if self.size() != (nw, nh): self.setFixedSize(nw, nh); self.label.setGeometry(0, self.header_spacing, px.width(), px.height())
        self.label.setPixmap(px); self.bar_xp.setGeometry(0, 0, self.width(), 4); self.emote_label.move((self.width()-60)//2, 10)
        self.happiness_gauge.move(self.width()-55, 10); self.bar_xp.raise_(); self.emote_label.raise_(); self.stats_panel.raise_(); self.happiness_gauge.raise_(); self.show()

    def enterEvent(self, e):
        self.stats_panel.move((self.width()-self.stats_panel.width())//2, self.height()-58); self.stats_panel.show(); self.bar_xp.show(); self.happiness_gauge.show()
    def leaveEvent(self, e): self.stats_panel.hide(); self.happiness_gauge.hide(); self.xp_hide_timer.start(2000)
    def show_emote(self, name):
        path = os.path.join(Settings.UI_DIR, f"{name}.png")
        if os.path.exists(path):
            self.emote_label.setPixmap(QPixmap(path).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)); self.emote_label.show(); self.emote_label.raise_(); QTimer.singleShot(3000, self.emote_label.hide)

    def contextMenuEvent(self, event):
        if self.engine:
            menu = QMenu(self); menu.setStyleSheet("QMenu { background-color: #252525; color: white; border: 1px solid #444; border-radius: 10px; padding: 5px; } QMenu::item:selected { background-color: #3d3d3d; color: #FFD700; }")
            menu.addAction("🎒  Інвентар").triggered.connect(self.engine.open_inventory)
            menu.addAction("🛒  Магазин").triggered.connect(self.engine.open_shop)
            if not self.engine.work_timer.isActive(): menu.addAction("📖  Навчання").triggered.connect(self.prompt_work_time)
            else: menu.addAction("🛑  Зупинити").triggered.connect(self.engine.stop_work_session)
            menu.addAction("⚔️  Тренування").triggered.connect(self.engine.train)
            sleep_t = "☀️  Прокинутись" if self.engine.current_state == "sleep" else "🌙  Лягти спати"
            menu.addAction(sleep_t).triggered.connect(self.engine.toggle_sleep)
            menu.addSeparator(); menu.addAction("❌  Вийти").triggered.connect(QCoreApplication.instance().quit)
            menu.exec(event.globalPos())

    def prompt_work_time(self):
        self.custom_input = ModernInputDialog(); self.custom_input.move(self.x()-50, self.y()-150); self.custom_input.show()
        self.check_input_timer = QTimer(); self.check_input_timer.timeout.connect(self.wait_for_input); self.check_input_timer.start(100)
    def wait_for_input(self):
        if self.custom_input and not self.custom_input.isVisible():
            self.check_input_timer.stop(); 
            if self.custom_input.result: self.engine.start_work_session(self.custom_input.result)
            self.custom_input.deleteLater(); self.custom_input = None
    def create_floating_text(self, text, color="#FFD700"):
        label = QLabel(text, self); label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 18px;")
        label.adjustSize(); x, y = (self.width()-label.width())//2, self.header_spacing+10; label.move(x, y); label.show()
        move = QPropertyAnimation(label, b"pos"); move.setDuration(1500); move.setStartValue(QPoint(x, y)); move.setEndValue(QPoint(x, y-70))
        eff = QGraphicsOpacityEffect(label); label.setGraphicsEffect(eff); fade = QPropertyAnimation(eff, b"opacity"); fade.setDuration(1500); fade.setStartValue(1.0); fade.setEndValue(0.0)
        group = QParallelAnimationGroup(self); group.addAnimation(move); group.addAnimation(fade); group.finished.connect(group.deleteLater); group.finished.connect(label.deleteLater); group.start()
    def update_timer_display(self, t):
        if t: self.timer_label.setText(t); self.timer_label.move((self.width()-70)//2, self.header_spacing-30); self.timer_label.show(); self.timer_label.raise_()
        else: self.timer_label.hide()
    def dragEnterEvent(self, e): e.accept() if e.mimeData().hasText() else e.ignore()
    def dropEvent(self, e):
        if self.engine: self.engine.use_item_from_inventory(e.mimeData().text())
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.is_dragging, self.press_pos = True, e.globalPosition().toPoint(); self.drag_pos = self.press_pos - self.frameGeometry().topLeft()
            if self.engine: self.engine.handle_drag_start()
    def mouseMoveEvent(self, e):
        if self.is_dragging: self.move(e.globalPosition().toPoint() - self.drag_pos)
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            if self.engine:
                if (e.globalPosition().toPoint() - self.press_pos).manhattanLength() < 5: self.engine.handle_click()
                else: self.engine.release_emotion()