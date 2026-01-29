import os
import logging

class Settings:
    PROJECT_NAME = "Asuna VPet Pro"
    LOG_LEVEL = logging.INFO
    
    # ТАЙМІНГИ (мс)
    TARGET_FPS = 60
    ANIMATION_SPEED = 125
    AI_THINK_INTERVAL = 5000       
    SAVE_INTERVAL = 60000          
    TIRED_REMIND_INTERVAL = 10000  # Кожні 10 сек нагадувати про втому
    
    # ПАРАМЕТРИ ПОВЕДІНКИ
    WALK_SPEED = 1.3
    STATS_DECAY_RATE = 0.005
    ENERGY_THRESHOLD_TIRED = 15.0  
    ENERGY_THRESHOLD_SLEEP = 5.0   
    XP_PER_TRAINING = 25
    LEVEL_UP_XP = 100
    
    # ГРАФІКА
    DEFAULT_SPRITE_HEIGHT = 200    
    
    # ШЛЯХИ
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ANIM_DIR = os.path.join(BASE_DIR, "assets", "animations")
    DATA_DIR = os.path.join(BASE_DIR, "assets", "data")
    SAVE_PATH = os.path.join(DATA_DIR, "stats.json")
    UI_DIR = os.path.join(BASE_DIR, "assets", "ui", "emotes")
    ICONS_DIR = os.path.join(BASE_DIR, "assets", "ui", "icons")

    # ВІДНОВЛЕННЯ
    FOOD_STATS = {"sandwich": 20, "hot-dog": 25, "sushi": 30, "fried-potatoes": 35, "pizza": 45, "pasta": 50}
    SWEET_STATS = {"lollipop": 10, "toffee": 15, "gummy-bear": 20, "chocolate": 25, "candy-apple": 30}