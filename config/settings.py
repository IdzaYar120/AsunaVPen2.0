import os

class Settings:
    PROJECT_NAME = "Asuna VPet Pro"
    TARGET_FPS = 60
    ANIMATION_SPEED = 125
    WALK_SPEED = 1.3
    
    # СТАТИСТИКА
    STATS_DECAY_RATE = 0.005
    XP_PER_TRAINING = 25      # Скільки XP дає одне тренування
    LEVEL_UP_XP = 100         # Скільки XP треба для нового рівня
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ANIM_DIR = os.path.join(BASE_DIR, "assets", "animations")
    DATA_DIR = os.path.join(BASE_DIR, "assets", "data")
    SAVE_PATH = os.path.join(DATA_DIR, "stats.json")
    UI_DIR = os.path.join(BASE_DIR, "assets", "ui", "emotes")
    ICONS_DIR = os.path.join(BASE_DIR, "assets", "ui", "icons")

    FOOD_STATS = {
        "sandwich": 20,
        "hot-dog": 25,
        "sushi": 30,
        "fried-potatoes": 35,
        "pizza": 45,
        "pasta": 50
    }
    SWEET_STATS = {
        "lollipop": 10,
        "toffee": 15,
        "gummy-bear": 20,
        "chocolate": 25,
        "candy-apple": 30
    }