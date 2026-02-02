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

    ESSENTIAL_ANIMS = ["idle", "walk_left", "walk_right", "drag", "sleep", "tired", "sad", "angry", "shy", "scared", "eat"]

    def load_essential(self):
        """Loads only the critical animations needed for startup."""
        if not os.path.exists(Settings.ANIM_DIR):
            logger.error(f"Animations directory missing: {Settings.ANIM_DIR}")
            return
            
        self.load_manifest()
        self.ref_h = int(Settings.DEFAULT_SPRITE_HEIGHT * Settings.SCALE_FACTOR)
        
        for name in self.ESSENTIAL_ANIMS:
            self.load_animation(name)
            
    def load_manifest(self):
        self.manifest = {}
        manifest_path = os.path.join(Settings.ANIM_DIR, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                import json
                with open(manifest_path, 'r') as f:
                    self.manifest = json.load(f)
                logger.info("Animation manifest loaded.")
            except Exception as e:
                logger.error(f"Failed to load manifest: {e}")

    def load_animation(self, name):
        """Loads a specific animation by name (folder name)."""
        if name in self.animations:
            return True # Already loaded
            
        path = os.path.join(Settings.ANIM_DIR, name)
        sheet_path = os.path.join(path, f"{name}.png")
        
        try:
            if os.path.exists(sheet_path):
                # Sheet Logic
                cfg = self.manifest.get(name, self.manifest.get("_default", {"rows": 2, "cols": 5}))
                rows = cfg.get("rows", 2)
                cols = cfg.get("cols", 5)
                if self.load_from_sheet(name, sheet_path, rows, cols):
                    return True
            
            elif os.path.exists(path) and os.path.isdir(path):
                # Sequence Logic
                frames = self._load_folder(path)
                if frames:
                    self.animations[name] = frames
                    logger.info(f"Loaded sequence: {name}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error loading animation '{name}': {e}")
            
        return False

    def unload_animation(self, name):
        """Unioads an animation to free memory."""
        if name in self.animations:
            del self.animations[name]
            logger.info(f"Unloaded animation: {name}")

    # Deprecated compatibility wrapper
    def load_all(self):
        self.load_essential()

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