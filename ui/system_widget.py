from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor, QFont

class SystemWidget(QWidget):
    def __init__(self, monitor, parent=None):
        super().__init__(parent) # Parent is typically None for independent window, or PetWindow logic logic handles it
        self.monitor = monitor
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(220, 260)
        
        # Interaction State
        self.is_dragging = False
        self.drag_pos = QPoint()
        
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(1000) # Update every second
        
    def init_ui(self):
        self.container = QWidget(self)
        self.container.setGeometry(5, 5, 210, 250)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 30, 220);
                border: 1px solid #00BFFF;
                border-radius: 10px;
            }
            QLabel {
                color: #00BFFF;
                font-family: 'Segoe UI';
                font-size: 12px;
                border: none;
                background: transparent;
            }
            QLabel.val {
                color: white;
                font-weight: bold;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #555;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FF4444;
            }
        """)
        
        layout = QVBoxLayout(self.container)
        
        # Header with Close Button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        
        head = QLabel("SYSTEM STATUS")
        head.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFD700;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.hide)
        
        header_layout.addStretch()
        header_layout.addWidget(head)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # CPU
        self.cpu_bar = self.create_row(layout, "CPU")
        
        # RAM
        self.ram_bar = self.create_row(layout, "RAM")
        self.ram_val = QLabel("0/0 GB")
        self.ram_val.setStyleSheet("color: #aaa; font-size: 10px; margin-left: 35px;")
        layout.addWidget(self.ram_val)
        
        # Disk
        d_layout = QHBoxLayout()
        d_layout.addWidget(QLabel("DISK (C:)"))
        self.disk_val = QLabel("Free: ...")
        self.disk_val.setProperty("class", "val")
        d_layout.addWidget(self.disk_val, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(d_layout)
        
        # Network
        n_layout = QVBoxLayout()
        self.net_down = QLabel("⬇️ 0 KB/s")
        self.net_up = QLabel("⬆️ 0 KB/s")
        self.net_down.setStyleSheet("color: #44FF44; font-size: 11px;")
        self.net_up.setStyleSheet("color: #FFAA44; font-size: 11px;")
        n_layout.addWidget(self.net_down)
        n_layout.addWidget(self.net_up)
        layout.addLayout(n_layout)
        
        # Battery (if available)
        self.bat_container = QWidget()
        b_layout = QHBoxLayout(self.bat_container)
        b_layout.setContentsMargins(0,0,0,0)
        b_layout.addWidget(QLabel("BATTERY"))
        self.bat_val = QLabel("100%")
        self.bat_val.setProperty("class", "val")
        b_layout.addWidget(self.bat_val, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.bat_container)
        
    def create_row(self, parent_layout, label):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFixedWidth(30)
        row.addWidget(lbl)
        
        bar = QProgressBar()
        bar.setFixedHeight(8)
        bar.setTextVisible(False)
        bar.setStyleSheet("""
            QProgressBar {
                background: #333;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #00BFFF;
                border-radius: 4px;
            }
        """)
        row.addWidget(bar)
        
        val = QLabel("0%")
        val.setFixedWidth(35)
        val.setAlignment(Qt.AlignmentFlag.AlignRight)
        val.setProperty("class", "val")
        row.addWidget(val)
        
        parent_layout.addLayout(row)
        
        # Store refs
        setattr(self, f"{label.lower()}_progress", bar)
        setattr(self, f"{label.lower()}_text", val)
        
        return bar

    def update_ui(self):
        stats = self.monitor.get_stats()
        
        # CPU
        self.cpu_progress.setValue(int(stats["cpu"]))
        self.cpu_text.setText(f"{int(stats['cpu'])}%")
        color = "#FF4444" if stats["cpu"] > 80 else "#00BFFF"
        self.cpu_progress.setStyleSheet(f"QProgressBar {{ background: #333; border-radius: 4px; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}")
        
        # RAM
        self.ram_progress.setValue(int(stats["ram_percent"]))
        self.ram_text.setText(f"{int(stats['ram_percent'])}%")
        self.ram_val.setText(stats["ram_text"])
        
        # Disk
        self.disk_val.setText(f"Free: {stats['disk_free']}")
        
        # Network (Convert)
        def fmt_speed(bytes_sec):
            if bytes_sec < 1024: return f"{int(bytes_sec)} B/s"
            elif bytes_sec < 1024**2: return f"{bytes_sec/1024:.1f} KB/s"
            else: return f"{bytes_sec/(1024**2):.1f} MB/s"
            
        self.net_down.setText(f"⬇️ {fmt_speed(stats['download'])}")
        self.net_up.setText(f"⬆️ {fmt_speed(stats['upload'])}")
        
        # Battery
        if stats["battery"] is not None:
            self.bat_container.show()
            icon = "🔌" if stats["plugged"] else "🔋"
            self.bat_val.setText(f"{icon} {stats['battery']}%")
        else:
            self.bat_container.hide()

    # Dragging Logic
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
