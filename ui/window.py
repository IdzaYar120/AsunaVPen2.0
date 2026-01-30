from PyQt6.QtWidgets import QWidget, QLabel, QProgressBar, QVBoxLayout, QMenu, QApplication, QGraphicsOpacityEffect, QInputDialog, QLineEdit, QPushButton, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QCoreApplication, QRectF, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QIntValidator, QImage
import os, time, random
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

class AchievementToast(QWidget):
    def __init__(self, name, icon_name, parent_win, offset_y=-80):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(220, 70)
        
        container = QFrame(self)
        container.setGeometry(0, 0, 220, 70)
        container.setStyleSheet("background: rgba(30,30,30,240); border: 2px solid #FFD700; border-radius: 12px;")
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10,5,10,5)
        
        icon = QLabel()
        icon.setFixedSize(45, 45)
        path = os.path.join(Settings.ICONS_DIR, icon_name)
        if os.path.exists(path):
            icon.setPixmap(QPixmap(path).scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(icon)
        
        vbox = QVBoxLayout()
        vbox.setSpacing(2)
        l1 = QLabel("🏆 ДОСЯГНЕННЯ!")
        l1.setStyleSheet("color: #FFD700; font-size: 10px; font-weight: bold; border:none; background:transparent;")
        l2 = QLabel(name)
        l2.setStyleSheet("color: white; font-size: 13px; font-weight: bold; border:none; background:transparent;")
        l2.setWordWrap(True)
        vbox.addWidget(l1); vbox.addWidget(l2)
        layout.addLayout(vbox)
        
        # Positioning
        screen_geo = QApplication.primaryScreen().availableGeometry()
        pet_geo = parent_win.frameGeometry()
        
        # Center relative to pet, vertically offset
        x = pet_geo.center().x() - self.width() // 2
        y = pet_geo.bottom() + 10 # Appears from bottom
        
        self.move(x, y)
        self.show()
        
        # Animation
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(1200)
        self.anim.setStartValue(QPoint(x, y))
        self.anim.setEndValue(QPoint(x, y + offset_y)) 
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close_anim)
        self.timer.start(4000)
        self.anim.start()
        
    def close_anim(self):
        self.anim_fade = QPropertyAnimation(self, b"windowOpacity")
        self.anim_fade.setDuration(800)
        self.anim_fade.setStartValue(1.0)
        self.anim_fade.setEndValue(0.0)
        self.anim_fade.finished.connect(self.deleteLater)
        self.anim_fade.start()

class SpeechBubble(QWidget):
    response_selected = pyqtSignal(str) # "happy", "neutral", "sad"

    def __init__(self, text, parent=None):
        super().__init__() # Independent window (no parent) for TopLevel behavior
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.parent_pet = parent # Reference for positioning
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Style Container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #333;
                border-radius: 10px;
            }
        """)
        c_layout = QVBoxLayout(container)
        
        # Text Label
        self.lbl = QLabel(text)
        self.lbl.setWordWrap(True)
        self.lbl.setStyleSheet("color: black; font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; border: none;")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(self.lbl)
        
        # Reaction Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 5, 0, 0)
        
        for emo, key in [("❤️", "happy"), ("😐", "neutral"), ("💔", "sad")]:
            btn = QPushButton(emo)
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: #f0f0f0; border: 1px solid #ccc; border-radius: 15px; font-size: 16px;
                }
                QPushButton:hover { background: #e0e0e0; border-color: #999; }
            """)
            btn.clicked.connect(lambda _, k=key: self.on_click(k))
            btn_layout.addWidget(btn)
            
        c_layout.addLayout(btn_layout)
        layout.addWidget(container)
        
        self.adjustSize()
        if self.width() > 200: self.setFixedWidth(200); self.adjustSize()
        self.show()
        
        # Fade Out Timer (long enough for user interaction)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fade_out)
        self.timer.start(8000)
        
    def on_click(self, key):
        self.timer.stop()
        self.response_selected.emit(key)
        self.fade_out()

    def fade_out(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()

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

class FloatingText(QWidget):
    def __init__(self, text, color, start_pos, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        lbl = QLabel(text, self)
        lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 18px;")
        lbl.adjustSize()
        self.setFixedSize(lbl.size())
        
        # Text Shadow via QGraphicsEffect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(2)
        shadow.setColor(QColor(0, 0, 0))
        shadow.setOffset(1, 1)
        lbl.setGraphicsEffect(shadow)
        
        self.move(start_pos)
        self.show()
        
        # Animation
        end_pos = QPoint(start_pos.x(), start_pos.y() - 80)
        
        self.anim_pos = QPropertyAnimation(self, b"pos")
        self.anim_pos.setDuration(2000)
        self.anim_pos.setStartValue(start_pos)
        self.anim_pos.setEndValue(end_pos)
        self.anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Use windowOpacity to avoid QPainter conflicts
        self.anim_fade = QPropertyAnimation(self, b"windowOpacity")
        self.anim_fade.setDuration(2000)
        self.anim_fade.setStartValue(1.0)
        self.anim_fade.setEndValue(0.0)
        
        self.group = QParallelAnimationGroup(self)
        self.group.addAnimation(self.anim_pos)
        self.group.addAnimation(self.anim_fade)
        self.group.finished.connect(self.deleteLater)
        self.group.start()

class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setAcceptDrops(True)
        self.header_spacing = int(80 * Settings.SCALE_FACTOR)
        self.label = QLabel(self); self.emote_label = QLabel(self); self.emote_label.setFixedSize(60, 60); self.emote_label.hide()
        self.bubble = None
        self.happiness_gauge = HappinessGauge(self); self.happiness_gauge.hide()
        self.timer_label = QLabel(self); self.timer_label.setFixedWidth(70); self.timer_label.hide()
        self.timer_label.setStyleSheet("background: rgba(0,0,0,160); color: #00FF00; font-weight: bold; border-radius: 8px;")
        
        # Level Badge
        self.level_badge = QLabel("Lvl 1", self)
        self.level_badge.setStyleSheet("""
            background: rgba(0, 0, 0, 150);
            color: #FFD700;
            font-weight: bold;
            font-size: 10px;
            border-radius: 5px;
            padding: 2px 5px;
        """)
        self.level_badge.adjustSize()
        self.level_badge.show()
        
        self.bar_xp = QProgressBar(self); self.bar_xp.setFixedHeight(4); self.bar_xp.hide()
        self.bar_xp.setStyleSheet("QProgressBar { border: none; background: rgba(0,0,0,80); } QProgressBar::chunk { background: #FFD700; }")
        self.stats_panel = QWidget(self); self.stats_panel.setFixedWidth(int(130*Settings.SCALE_FACTOR+50)); self.stats_panel.setFixedHeight(55); self.stats_panel.hide()
        layout = QVBoxLayout(self.stats_panel); self.bar_hunger = self.create_bar("#FF4444"); self.bar_energy = self.create_bar("#44FF44"); self.bar_health = self.create_bar("#4444FF")
        for b in [self.bar_hunger, self.bar_energy, self.bar_health]: layout.addWidget(b)
        self.is_dragging, self.drag_pos, self.press_pos = False, QPoint(), QPoint()
        self.xp_hide_timer = QTimer(); self.xp_hide_timer.setSingleShot(True); self.xp_hide_timer.timeout.connect(self.bar_xp.hide)
        self.emote_timer = QTimer(); self.emote_timer.setSingleShot(True); self.emote_timer.timeout.connect(self.emote_label.hide)
        self.custom_input = None
        self.first_render = True

    def create_bar(self, color):
        bar = QProgressBar(); bar.setFixedHeight(5); bar.setTextVisible(False)
        bar.setStyleSheet(f"QProgressBar {{ border-radius: 2px; background: rgba(0,0,0,150); }} QProgressBar::chunk {{ background: {color}; }}")
        return bar

    def update_stats_ui(self, h, e, hl, hap, max_val=100.0):
        # Update progress ranges
        for bar in [self.bar_hunger, self.bar_energy]:
            if bar.maximum() != int(max_val): bar.setRange(0, int(max_val))
            
        self.bar_hunger.setValue(int(h)); self.bar_energy.setValue(int(e)); self.bar_health.setValue(int(hl))
        self.happiness_gauge.value = hap; self.happiness_gauge.update()

    def update_xp_ui(self, xp, lvl, max_xp=100, force_show=False):
        if self.bar_xp.maximum() != int(max_xp): self.bar_xp.setRange(0, int(max_xp))
        self.bar_xp.setValue(int(xp))
        
        # Update Level Badge
        self.level_badge.setText(f"Lvl {lvl}")
        self.level_badge.adjustSize()
        self.level_badge.move(self.width() - self.level_badge.width() - 5, self.height() - 20)
        self.level_badge.raise_()
        
        if force_show: self.bar_xp.show(); self.xp_hide_timer.start(5000)

    def render_pet(self, px):
        # Add 25px bottom padding for shadow
        nw, nh = px.width(), px.height() + self.header_spacing + 25
        if self.size() != (nw, nh): self.setFixedSize(nw, nh)
        
        self.label.setGeometry(0, self.header_spacing, px.width(), px.height())
        self.label.setPixmap(px)
        
        self.bar_xp.setGeometry(0, 0, self.width(), 4)
        self.emote_label.move((self.width()-60)//2, 10)
        self.happiness_gauge.move(self.width()-55, 10)
        
        self.bar_xp.raise_()
        self.emote_label.raise_()
        self.stats_panel.raise_()
        self.happiness_gauge.raise_()
        
        if self.first_render:
            screen = QApplication.primaryScreen().availableGeometry()
            # Center horizontally, bottom aligned to taskbar
            x = (screen.width() - nw) // 2
            y = screen.height() - nh
            self.move(x, y)
            self.first_render = False
        
        self.show()
        self.update() # Trigger repaint for shadow

    def paintEvent(self, event):
        # Shadow Rendering
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 60)) 
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Centered bottom ellipse
        shadow_width = self.width() * 0.7
        shadow_height = 12
        x = (self.width() - shadow_width) // 2
        
        # Draw in the extra padding space (last 25px)
        y = self.height() - shadow_height - 5
        
        painter.drawEllipse(QRectF(x, y, shadow_width, shadow_height))

    def enterEvent(self, e):
        self.stats_panel.move((self.width()-self.stats_panel.width())//2, self.height()-58); self.stats_panel.show(); self.bar_xp.show(); self.happiness_gauge.show()
    def leaveEvent(self, e): self.stats_panel.hide(); self.happiness_gauge.hide(); self.xp_hide_timer.start(2000)
    def show_emote(self, name):
        path = os.path.join(Settings.UI_DIR, f"{name}.png")
        if os.path.exists(path):
            self.emote_label.setPixmap(QPixmap(path).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)); self.emote_label.show(); self.emote_label.raise_()
            self.emote_timer.stop()
            self.emote_timer.start(3000)

    def show_bubble(self, text):
        if self.bubble:
            try:
                self.bubble.deleteLater()
            except RuntimeError:
                pass
        
        self.bubble = SpeechBubble(text, self)
        self.bubble.response_selected.connect(self.engine.handle_response)
        self.bubble.destroyed.connect(lambda: setattr(self, 'bubble', None))
        
        # Center bubble (Global Coordinates)
        self.bubble.adjustSize()
        self.bubble.show() # Show first to calculate size
        
        global_pos = self.mapToGlobal(QPoint(0, 0))
        x = global_pos.x() + (self.width() - self.bubble.width()) // 2
        y = global_pos.y() + self.header_spacing - self.bubble.height() - 10
        
        # Screen Boundary Check
        screen_geo = QApplication.primaryScreen().availableGeometry()
        
        # Right Boundary
        if x + self.bubble.width() > screen_geo.right() - 10:
            x = screen_geo.right() - self.bubble.width() - 10
        
        # Left Boundary
        if x < screen_geo.left() + 10:
            x = screen_geo.left() + 10
            
        self.bubble.move(int(x), int(y))

    def contextMenuEvent(self, event):
        if self.engine:
            menu = QMenu(self); menu.setStyleSheet("QMenu { background-color: #252525; color: white; border: 1px solid #444; border-radius: 10px; padding: 5px; } QMenu::item:selected { background-color: #3d3d3d; color: #FFD700; }")
            menu.addAction("🎒  Інвентар").triggered.connect(self.engine.open_inventory)
            menu.addAction("🛒  Магазин").triggered.connect(self.engine.open_shop)
            menu.addAction("🏆  Досягнення").triggered.connect(self.engine.open_achievements)
            menu.addAction("🗣️  Чат (AI)").triggered.connect(self.engine.open_chat)
            
            # Games Submenu
            games_menu = menu.addMenu("🎮  Міні-ігри")
            games_menu.setStyleSheet(menu.styleSheet())
            games_menu.addAction("💰  Полювання за монетами").triggered.connect(self.engine.open_minigame)
            games_menu.addAction("🎰  Ігрові автомати").triggered.connect(self.engine.open_slots)
            
            if not self.engine.work_timer.isActive(): menu.addAction("📖  Навчання").triggered.connect(self.prompt_work_time)
            else: menu.addAction("🛑  Зупинити").triggered.connect(self.engine.stop_work_session)
            menu.addAction("📝  Список справ").triggered.connect(self.engine.open_todo_list)
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
        # Determine global coordinates
        g_pos = self.mapToGlobal(QPoint(0, 0))
        
        # Random offset to avoid overlap with emotion/previous text
        # Offset more to the sides (left or right of heavy)
        offset_x = random.choice([-1, 1]) * random.randint(40, 70)
        
        x = g_pos.x() + (self.width() // 2) + offset_x - 30 # -30 is approx half text width
        y = g_pos.y() + self.header_spacing + 20
        
        # Create independent text window
        # We don't store reference, it deletes itself after anim
        # But to prevent GC, store in active_texts list.
        ft = FloatingText(text, color, QPoint(x, y), None) 
        
        if not hasattr(self, 'active_texts'): self.active_texts = []
        self.active_texts.append(ft)
        ft.destroyed.connect(lambda: self.active_texts.remove(ft) if ft in self.active_texts else None)

    def show_achievement_popup(self, name, icon_name):
        # Use new class for flying toast window
        self.ach_toast = AchievementToast(name, icon_name, self, offset_y=-100)
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
                else: 
                    self.engine.release_emotion()
                    self.apply_gravity()

    def apply_gravity(self):
        screen_geo = QApplication.primaryScreen().availableGeometry()
        floor_y = screen_geo.height() - self.height()
        
        # If pet is above floor (with 10px tolerance)
        if self.y() < floor_y - 10:
            self.anim_grav = QPropertyAnimation(self, b"pos")
            self.anim_grav.setDuration(3000) # 3 seconds duration (Slow fall)
            self.anim_grav.setStartValue(self.pos())
            self.anim_grav.setEndValue(QPoint(self.x(), floor_y))
            self.anim_grav.setEasingCurve(QEasingCurve.Type.OutBounce)
            self.anim_grav.start()

    def position_window(self, win):
        """Center window on screen."""
        screen_geo = QApplication.primaryScreen().availableGeometry()
        win_geo = win.frameGeometry()
        x = (screen_geo.width() - win_geo.width()) // 2
        y = (screen_geo.height() - win_geo.height()) // 2
        win.move(x, y)