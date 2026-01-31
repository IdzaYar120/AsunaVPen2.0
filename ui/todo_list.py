from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QLabel, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor

class TodoWindow(QWidget):
    def __init__(self, task_manager, engine):
        super().__init__()
        self.task_manager = task_manager
        self.engine = engine
        self.setWindowTitle("Quests")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.resize(320, 450)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.init_ui()
        self.refresh_list()
        
    def init_ui(self):
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 320, 450)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 15px;
            }
        """)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("🌟 БАЖАННЯ (КВЕСТИ)")
        title.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 14px; border: none;")
        close_btn = QPushButton("×")
        close_btn.setFixedSize(25, 25)
        close_btn.setStyleSheet("""
            QPushButton { color: #aaa; font-size: 18px; border: none; font-weight: bold; background: transparent; }
            QPushButton:hover { color: #fff; }
        """)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        main_layout.addLayout(header_layout)
        
        # Забираємо поле вводу, бо квести дає асуна
        
        # List
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: transparent;
                margin-bottom: 5px;
            }
        """)
        self.task_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        main_layout.addWidget(self.task_list)
        
        self.old_pos = None

    def refresh_list(self):
        self.task_list.clear()
        quests = self.task_manager.stats.data.get("tasks", [])
        
        if not quests:
            item = QListWidgetItem()
            lbl = QLabel("Поки що немає бажань...\nЧекай, скоро з'являться!")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #888; font-style: italic; border: none;")
            item.setSizeHint(QSize(280, 100))
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, lbl)
            return

        for q in quests:
            item = QListWidgetItem()
            
            widget = QWidget()
            widget.setStyleSheet("""
                QWidget {
                    background-color: #383838;
                    border-radius: 8px;
                }
                QLabel { border: none; color: #eee; font-size: 13px; }
            """)
            
            w_layout = QVBoxLayout(widget)
            w_layout.setContentsMargins(10, 10, 10, 10)
            
            # Верхній рядок: Текст + Кнопка видалення
            top_layout = QHBoxLayout()
            label = QLabel(self.engine._t(q['text']))
            label.setWordWrap(True)
            
            del_btn = QPushButton("×")
            del_btn.setFixedSize(20, 20)
            del_btn.setToolTip("Відмовитись")
            del_btn.setFlat(True)
            del_btn.setStyleSheet("color: #666; font-weight: bold; border: none; font-size: 16px;")
            del_btn.clicked.connect(lambda _, t_id=q["id"]: self.delete_task(t_id))
            
            top_layout.addWidget(label)
            top_layout.addWidget(del_btn)
            w_layout.addLayout(top_layout)
            
            # Нижній рядок: Прогрес бар
            cur, req = q.get("current_count", 0), q.get("required_count", 1)
            
            bar = QProgressBar()
            bar.setRange(0, req)
            bar.setValue(cur)
            bar.setTextVisible(True)
            bar.setFormat(f"%v / %m")
            bar.setFixedHeight(12)
            bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    background-color: #222;
                    border-radius: 6px;
                    color: white;
                    font-size: 9px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #FFD700;
                    border-radius: 6px;
                }
            """)
            
            w_layout.addWidget(bar)
            
            item.setSizeHint(QSize(widget.sizeHint().width(), 70))
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, widget)
            
    def delete_task(self, task_id):
        self.task_manager.remove_task(task_id)
        self.refresh_list()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
