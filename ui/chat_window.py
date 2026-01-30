from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QInputDialog, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QThread

class AIWorker(QThread):
    finished = pyqtSignal(str)
    
    def __init__(self, engine, text):
        super().__init__()
        self.engine = engine
        self.text = text
        
    def run(self):
        if self.engine.ai.is_ready:
            try:
                response = self.engine.ai.get_response(self.text)
                self.finished.emit(response if response else "...")
            except:
                self.finished.emit("Error")
        else:
            self.finished.emit("AI_NOT_READY")

class ChatWindow(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("Чат з Асуною")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(350, 450)
        self.setStyleSheet("background-color: #2b2b2b; color: white; font-family: 'Segoe UI';")
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("💬 AI Chat")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")
        
        settings_btn = QPushButton("⚙️ API Key")
        settings_btn.setFixedSize(80, 25)
        settings_btn.setStyleSheet("background: #444; border-radius: 5px;")
        settings_btn.clicked.connect(self.prompt_api_key)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(settings_btn)
        layout.addLayout(header)
        
        # Chat History
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 8px; padding: 5px; font-size: 13px;")
        layout.addWidget(self.history)
        
        # Input Area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Напиши щось (наприклад: 'Привіт')...")
        self.input_field.setStyleSheet("background: #333; border: 1px solid #555; border-radius: 15px; padding: 5px 10px; color: white;")
        self.input_field.returnPressed.connect(self.send_message)
        
        send_btn = QPushButton("➤")
        send_btn.setFixedSize(35, 35)
        send_btn.setStyleSheet("background: #FFD700; color: black; border-radius: 17px; font-weight: bold;")
        send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)
        
        # Initial Message
        if not self.engine.ai.is_ready:
            self.add_message("System", "Щоб почати спілкування, введи Google Gemini API Key у налаштуваннях (⚙️).")
        else:
            self.add_message("Asuna", "Привіт! Про що поговоримо? 😊")
            
        self.worker = None

    def send_message(self):
        text = self.input_field.text().strip()
        if not text: return
        
        self.add_message("You", text)
        self.input_field.clear()
        self.input_field.setDisabled(True) # Prevent spam
        
        # Start Worker Thread
        self.worker = AIWorker(self.engine, text)
        self.worker.finished.connect(self.handle_ai_response)
        self.worker.start()

    def handle_ai_response(self, response):
        if response == "AI_NOT_READY":
             self.add_message("System", "AI не підключено.")
        elif response == "Error":
             self.add_message("System", "Помилка з'єднання.")
        else:
            self.add_message("Asuna", response)
            self.engine.talk_text(response) # Show bubble
            
        self.input_field.setDisabled(False)
        self.input_field.setFocus()
        self.worker = None

    def add_message(self, sender, text):
        color = "#FFD700" if sender == "Asuna" else "#4CAF50" if sender == "You" else "#888"
        self.history.append(f"<b style='color:{color}'>{sender}:</b> {text}")
        
    def prompt_api_key(self):
        key, ok = QInputDialog.getText(self, "Gemini API Key", "Введи API ключ (з aistudio.google.com):")
        if ok and key:
            if self.engine.set_api_key(key):
                self.add_message("System", "Ключ прийнято! ✅ Тепер ми можемо говорити.")
            else:
                self.add_message("System", "Помилка ключа ❌")
