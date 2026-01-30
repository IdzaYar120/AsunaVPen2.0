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

        # Estimate Ref H (Generic fallback or based on first sheet)
        # We'll use default since sheets might vary in size
        self.ref_h = int(Settings.DEFAULT_SPRITE_HEIGHT * Settings.SCALE_FACTOR)
        
        for folder in os.listdir(Settings.ANIM_DIR):
            path = os.path.join(Settings.ANIM_DIR, folder)
            if os.path.isdir(path):
                # Check for Sprite Sheet (convention: foldername.png inside folder)
                sheet_path = os.path.join(path, f"{folder}.png")
                
            try:
                if os.path.exists(sheet_path):
                    # Default: 2 rows, 5 cols
                    rows, cols = 2, 5
                    if folder in ["training", "sing"]: cols = 4 
                    if folder in ["eat", "tired", "sad", "angry"]: rows, cols = 1, 5
                    if folder in ["drag"]: rows, cols = 2, 3
                    if folder in ["scared", "shy"]: rows, cols = 1, 6
                    if folder in ["excited", "dance", "playing", "working"]: cols = 3 
                    if folder == "sleep": cols = 2
                    
                    # Specific Overrides
                    if folder in ["idle", "walk_left", "walk_right", "drag"]: rows, cols = 2, 3
                    if folder == "training": rows, cols = 2, 5 
                    
                    if not self.load_from_sheet(folder, sheet_path, rows, cols):
                        logger.warning(f"Failed to load sprite sheet: {folder}")
                else:
                    # Fallback to Sequence Loading
                    frames = self._load_folder(path)
                    if frames:
                        self.animations[folder] = frames
                        logger.info(f"Loaded sequence: {folder}")
                    else:
                        logger.warning(f"No valid frames found for: {folder}")
            except Exception as e:
                logger.error(f"Error loading animation '{folder}': {e}")

    def _determine_reference_height(self):
        """Шукає walk_right або перше доступне зображення"""
        walk_path = os.path.join(Settings.ANIM_DIR, "walk_right")
        check_list = [walk_path] + [os.path.join(Settings.ANIM_DIR, d) for d in os.listdir(Settings.ANIM_DIR)]
        for path in check_list:
            if os.path.exists(path) and os.path.isdir(path):
                for f in os.listdir(path):
                    if f.lower().endswith('.png'):
                        px = QPixmap(os.path.join(path, f))
                        if not px.isNull(): return px.height()
        # Fallback до константи з Settings
        return Settings.DEFAULT_SPRITE_HEIGHT

    def _load_folder(self, path):
        frames = []
        folder_name = os.path.basename(path)
        scale_mult = Settings.ANIMATION_SCALES.get(folder_name, 1.0)
        target_h = int(self.ref_h * scale_mult)
        
        # Calculate canvas size dynamically
        canvas_dim = int(target_h + (60 * Settings.SCALE_FACTOR * scale_mult))
        canvas_size = QSize(canvas_dim, canvas_dim)
        
        for f in sorted([file for file in os.listdir(path) if file.lower().endswith('.png')]):
            raw = QPixmap(os.path.join(path, f))
            if raw.isNull(): continue
            scaled = raw.scaledToHeight(target_h, Qt.TransformationMode.SmoothTransformation)
            canvas = QPixmap(canvas_size)
            canvas.fill(Qt.GlobalColor.transparent)
            painter = QPainter(canvas)
            painter.drawPixmap((canvas_size.width()-scaled.width())//2, canvas_size.height()-scaled.height(), scaled)
            painter.end()
            frames.append(canvas)
        return frames

    def get_frames(self, state): return self.animations.get(state, [])

    def load_from_sheet(self, name, path, rows, cols):
        """Loads animation from a sprite sheet."""
        if not os.path.exists(path):
            logger.error(f"Sprite sheet not found: {path}")
            return False
            
        sheet = QPixmap(path)
        if sheet.isNull(): return False
        
        frame_w = sheet.width() // cols
        frame_h = sheet.height() // rows
        
        logger.info(f"Loading '{name}' Sheet: {sheet.width()}x{sheet.height()} -> {rows}x{cols} ({frame_w}x{frame_h} per frame)")
        
        frames = []
        
        # Calculate target height and canvas size
        scale_mult = Settings.ANIMATION_SCALES.get(name, 1.0)
        target_h = int(self.ref_h * scale_mult)
        
        canvas_dim = int(target_h + (60 * Settings.SCALE_FACTOR * scale_mult))
        canvas_size = QSize(canvas_dim, canvas_dim)
        
        for r in range(rows):
            for c in range(cols):
                # Crop frame
                cropped = sheet.copy(c * frame_w, r * frame_h, frame_w, frame_h)
                
                # Scale and Center
                scaled = cropped.scaledToHeight(target_h, Qt.TransformationMode.SmoothTransformation)
                canvas = QPixmap(canvas_size)
                canvas.fill(Qt.GlobalColor.transparent)
                painter = QPainter(canvas)
                
                # Center horizontally, bottom align
                x = (canvas_size.width() - scaled.width()) // 2
                y = canvas_size.height() - scaled.height()
                
                painter.drawPixmap(x, y, scaled)
                painter.end()
                frames.append(canvas)
                
        self.animations[name] = frames
        logger.info(f"Loaded sprite sheet: {name} ({len(frames)} frames)")
        return True