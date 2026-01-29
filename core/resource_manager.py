import os
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import Qt, QSize
from config.settings import Settings

class ResourceManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.animations = {}
            cls._instance.canvas_size = QSize(0, 0)
            cls._instance.reference_height = 0 # Еталонна висота
        return cls._instance

    def load_all(self):
        if not os.path.exists(Settings.ANIM_DIR): return

        # 1. Знаходимо еталонну висоту (беремо з ходьби, як ви просили)
        walk_ref_path = os.path.join(Settings.ANIM_DIR, "walk_right")
        if os.path.exists(walk_ref_path):
            files = [f for f in os.listdir(walk_ref_path) if f.lower().endswith('.png')]
            if files:
                ref_px = QPixmap(os.path.join(walk_ref_path, files[0]))
                self.reference_height = ref_px.height()
                print(f"Еталонна висота (з ходьби): {self.reference_height}px")

        # 2. Визначаємо розмір полотна (трохи більше за еталон)
        # Навіть якщо інші картинки були великі, ми їх зменшимо до reference_height
        self.canvas_size = QSize(self.reference_height + 50, self.reference_height + 50)

        # 3. Завантажуємо та масштабуємо всі анімації
        for folder_name in os.listdir(Settings.ANIM_DIR):
            folder_path = os.path.join(Settings.ANIM_DIR, folder_name)
            if os.path.isdir(folder_path):
                frames = []
                file_list = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.png')])
                
                for f in file_list:
                    raw_px = QPixmap(os.path.join(folder_path, f))
                    if raw_px.isNull(): continue
                    
                    # МАСШТАБУВАННЯ: Підганяємо картинку під еталонну висоту
                    # SmoothTransformation забезпечує високу якість (немає "пікселів")
                    scaled_px = raw_px.scaledToHeight(
                        self.reference_height, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    # Малюємо на прозорому полотні (вирівнювання по низу)
                    canvas = QPixmap(self.canvas_size)
                    canvas.fill(Qt.GlobalColor.transparent)
                    
                    painter = QPainter(canvas)
                    x = (self.canvas_size.width() - scaled_px.width()) // 2
                    y = self.canvas_size.height() - scaled_px.height()
                    painter.drawPixmap(x, y, scaled_px)
                    painter.end()
                    
                    frames.append(canvas)
                
                if frames:
                    self.animations[folder_name] = frames
                    print(f"Оптимізовано стан: {folder_name}")

    def get_frames(self, state_name):
        return self.animations.get(state_name, [])