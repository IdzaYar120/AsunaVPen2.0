import os
import logging
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import Qt, QSize
from config.settings import Settings

logger = logging.getLogger(__name__)

class ResourceManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.animations = {}
            cls._instance.ref_h = 0
        return cls._instance

    def load_all(self):
        if not os.path.exists(Settings.ANIM_DIR):
            logger.error(f"Animations directory missing: {Settings.ANIM_DIR}")
            return

        self.ref_h = self._determine_reference_height()
        canvas_size = QSize(self.ref_h + 60, self.ref_h + 60)

        for folder in os.listdir(Settings.ANIM_DIR):
            path = os.path.join(Settings.ANIM_DIR, folder)
            if os.path.isdir(path):
                frames = self._load_folder(path, canvas_size)
                if frames:
                    self.animations[folder] = frames
                    logger.info(f"Loaded: {folder} ({len(frames)} frames)")

    def _determine_reference_height(self):
        walk_path = os.path.join(Settings.ANIM_DIR, "walk_right")
        check_list = [walk_path] + [os.path.join(Settings.ANIM_DIR, d) for d in os.listdir(Settings.ANIM_DIR)]
        for path in check_list:
            if os.path.exists(path) and os.path.isdir(path):
                for f in os.listdir(path):
                    if f.lower().endswith('.png'):
                        px = QPixmap(os.path.join(path, f))
                        if not px.isNull(): return px.height()
        return Settings.DEFAULT_SPRITE_HEIGHT

    def _load_folder(self, path, canvas_size):
        frames = []
        for f in sorted([file for file in os.listdir(path) if file.lower().endswith('.png')]):
            raw = QPixmap(os.path.join(path, f))
            if raw.isNull(): continue
            scaled = raw.scaledToHeight(self.ref_h, Qt.TransformationMode.SmoothTransformation)
            canvas = QPixmap(canvas_size)
            canvas.fill(Qt.GlobalColor.transparent)
            painter = QPainter(canvas)
            painter.drawPixmap((canvas_size.width()-scaled.width())//2, canvas_size.height()-scaled.height(), scaled)
            painter.end()
            frames.append(canvas)
        return frames

    def get_frames(self, state): return self.animations.get(state, [])