from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, 
    QComboBox, QLineEdit, QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from config.settings import Settings

class SettingsWindow(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setWindowTitle("Налаштування")
        self.setFixedSize(400, 500)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: white;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                font-size: 14px;
            }
            QFrame.section {
                background-color: #252525;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 5px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 8px;
                background: #333;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #FFD700;
                border: 1px solid #FFD700;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit {
                background: #333;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 4px;
                color: white;
                min-height: 20px;
            }
            QComboBox {
                background: #333;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 4px;
                color: white;
                min-height: 20px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header (Fixed)
        header = QLabel("⚙️ Налаштування")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFD700; margin-top: 10px; margin-bottom: 5px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 4px;
            }
        """)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget) # This replaces the old 'layout'
        layout.setSpacing(15) # Increased spacing
        layout.setContentsMargins(20, 10, 20, 10)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # --- AUDIO ---
        audio_frame = QFrame(); audio_frame.setProperty("class", "section")
        vbox_audio = QVBoxLayout(audio_frame)
        
        lbl_audio = QLabel("🔊 Звук")
        lbl_audio.setStyleSheet("font-weight: bold; color: #BBB;")
        vbox_audio.addWidget(lbl_audio)
        
        # SFX
        hbox_sfx = QHBoxLayout()
        hbox_sfx.addWidget(QLabel("Ефекти:"))
        self.slider_sfx = QSlider(Qt.Orientation.Horizontal)
        self.slider_sfx.setRange(0, 100)
        self.slider_sfx.setValue(Settings.VOLUME_SFX)
        self.slider_sfx.valueChanged.connect(self.on_sfx_change)
        hbox_sfx.addWidget(self.slider_sfx)
        self.lbl_sfx_val = QLabel(f"{Settings.VOLUME_SFX}%")
        self.lbl_sfx_val.setFixedWidth(35)
        hbox_sfx.addWidget(self.lbl_sfx_val)
        vbox_audio.addLayout(hbox_sfx)

        # Music
        hbox_music = QHBoxLayout()
        hbox_music.addWidget(QLabel("Музика:"))
        self.slider_music = QSlider(Qt.Orientation.Horizontal)
        self.slider_music.setRange(0, 100)
        self.slider_music.setValue(Settings.VOLUME_MUSIC)
        self.slider_music.valueChanged.connect(self.on_music_change)
        hbox_music.addWidget(self.slider_music)
        self.lbl_music_val = QLabel(f"{Settings.VOLUME_MUSIC}%")
        self.lbl_music_val.setFixedWidth(35)
        hbox_music.addWidget(self.lbl_music_val)
        vbox_audio.addLayout(hbox_music)
        
        layout.addWidget(audio_frame)

        # --- GENERAL ---
        gen_frame = QFrame(); gen_frame.setProperty("class", "section")
        vbox_gen = QVBoxLayout(gen_frame)
        
        lbl_gen = QLabel("🌍 Загальні")
        lbl_gen.setStyleSheet("font-weight: bold; color: #BBB;")
        vbox_gen.addWidget(lbl_gen)
        
        # Language
        hbox_lang = QHBoxLayout()
        hbox_lang.addWidget(QLabel("Мова:"))
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Українська (UK)", "English (EN)"])
        self.combo_lang.setCurrentIndex(0 if Settings.LANGUAGE == "uk" else 1)
        self.combo_lang.currentIndexChanged.connect(self.on_lang_change)
        hbox_lang.addWidget(self.combo_lang)
        vbox_gen.addLayout(hbox_lang)
        
        # Startup
        self.chk_startup = QCheckBox("Запускати з Windows")
        self.chk_startup.setChecked(Settings.RUN_ON_STARTUP)
        self.chk_startup.stateChanged.connect(self.on_startup_change)
        vbox_gen.addWidget(self.chk_startup)
        
        layout.addWidget(gen_frame)

        # --- AI ---
        ai_frame = QFrame(); ai_frame.setProperty("class", "section")
        vbox_ai = QVBoxLayout(ai_frame)
        vbox_ai.setSpacing(10) # Specific spacing for AI section
        
        lbl_ai = QLabel("🧠 Штучний Інтелект")
        lbl_ai.setStyleSheet("font-weight: bold; color: #BBB;")
        vbox_ai.addWidget(lbl_ai)
        
        vbox_ai.addWidget(QLabel("Gemini API Key:"))
        self.inp_api = QLineEdit()
        self.inp_api.setPlaceholderText("Вставте ключ тут...")
        self.inp_api.setEchoMode(QLineEdit.EchoMode.Password)
        if self.engine.stats.data.get("gemini_api_key"):
            self.inp_api.setText(self.engine.stats.data.get("gemini_api_key"))
        vbox_ai.addWidget(self.inp_api)
        
        btn_save_api = QPushButton("Зберегти API Key")
        btn_save_api.clicked.connect(self.save_api)
        vbox_ai.addWidget(btn_save_api)
        
        layout.addWidget(ai_frame)
        
        layout.addStretch()
        
        # Close Button (Outside scroll)
        btn_close = QPushButton("Закрити")
        btn_close.clicked.connect(self.hide)
        btn_close.setStyleSheet("background-color: #555; margin: 10px; min-height: 25px;")
        main_layout.addWidget(btn_close)

    def on_sfx_change(self, val):
        self.lbl_sfx_val.setText(f"{val}%")
        self.engine.sound.set_global_volume(val)
        # Verify sound (play click if diff > 5 to avoid spam)
        # self.engine.sound.play("click") 
        
    def on_music_change(self, val):
        self.lbl_music_val.setText(f"{val}%")
        Settings.VOLUME_MUSIC = val
        self.engine.music_player.set_volume(val / 100.0)

    def on_lang_change(self, idx):
        lang_code = "uk" if idx == 0 else "en"
        Settings.LANGUAGE = lang_code
        self.engine.window.create_floating_text("Language changed (Restart required)", "white")
        
    def on_startup_change(self, state):
        is_checked = (state == 2) # Qt.CheckState.Checked
        Settings.RUN_ON_STARTUP = is_checked
        # Logic to write to registry would go here or in engine
        self.engine.toggle_startup(is_checked)

    def save_api(self):
        key = self.inp_api.text().strip()
        if key:
            self.engine.stats.data["gemini_api_key"] = key
            self.engine.ai.init_ai(key)
            self.engine.window.create_floating_text("API Key Saved! ✅", "#4CAF50")
            self.engine.stats.save_stats()
