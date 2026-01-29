import os, logging

class Settings:
    PROJECT_NAME = "Asuna VPet Pro"
    LOG_LEVEL = logging.INFO
    TARGET_FPS = 60
    ANIMATION_SPEED = 125
    AI_THINK_INTERVAL = 5000       
    TIRED_REMIND_INTERVAL = 10000  
    WALK_SPEED = 1.3
    SCALE_FACTOR = 0.5
    DEFAULT_SPRITE_HEIGHT = 200    

    # --- БАЛАНС ВИТРАТ ---
    STATS_DECAY_BASE = 0.003
    ENERGY_DECAY_IDLE, ENERGY_DECAY_WALK, ENERGY_DECAY_WORK = 0.05, 0.2, 0.5
    
    # --- ЛОГІКА ЩАСТЯ ---
    HAPPINESS_DECAY_IDLE = 0.002
    HAPPINESS_DECAY_TRAIN = 0.015
    HAPPINESS_DECAY_WORK = 0.008
    HAPPINESS_DECAY_ANGRY = 0.02
    HAPPINESS_DECAY_NEGLECT = 0.01
    NEGLECT_THRESHOLD = 300 # 5 хвилин
    HAPPINESS_THRESHOLD_SAD = 25.0

    ENERGY_THRESHOLD_TIRED, ENERGY_THRESHOLD_SLEEP = 15.0, 5.0
    XP_PER_TRAINING, LEVEL_UP_XP, COINS_PER_TRAINING = 25, 100, 15
    PLAY_XP_REWARD = 10

    # МАГАЗИН
    SHOP_PRICES = {
        "sandwich": 10, "pizza": 40, "lollipop": 5, "chocolate": 12,
        "ball": 30, "joystick": 60,
        "flowers": 25, "teddy-bear": 55, "sword-gift": 100, "crown": 250
    }
    FOOD_STATS = {"sandwich": 20, "hot-dog": 25, "sushi": 30, "fried-potatoes": 35, "pizza": 45, "pasta": 50}
    SWEET_STATS = {"lollipop": 10, "toffee": 15, "gummy-bear": 20, "chocolate": 25, "candy-apple": 30}
    GIFT_STATS = {"flowers": 25, "teddy-bear": 50, "sword-gift": 80, "crown": 100}
    PLAY_ITEMS = ["ball", "joystick"]

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ANIM_DIR = os.path.join(BASE_DIR, "assets", "animations")
    DATA_DIR = os.path.join(BASE_DIR, "data")
    SAVE_PATH = os.path.join(DATA_DIR, "stats.json")
    UI_DIR = os.path.join(BASE_DIR, "assets", "ui", "emotes")
    ICONS_DIR = os.path.join(BASE_DIR, "assets", "ui", "icons")