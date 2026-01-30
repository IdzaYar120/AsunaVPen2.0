import os, logging

class Settings:
    PROJECT_NAME = "Asuna VPet Pro"
    LOG_LEVEL = logging.INFO
    TARGET_FPS = 60
    ANIMATION_SPEED = 250
    AI_THINK_INTERVAL = 5000       
    TIRED_REMIND_INTERVAL = 10000  
    WALK_SPEED = 1.3
    
    # AI CONFIG
    GEMINI_API_KEY = "" # User will paste key here or via UI
    SCALE_FACTOR = 0.85
    DEFAULT_SPRITE_HEIGHT = 200    

    DEFAULT_SPRITE_HEIGHT = 200    
    
    # --- EXPENSES BALANCE ---
    STATS_DECAY_BASE = 0.003
    ENERGY_DECAY_IDLE, ENERGY_DECAY_WALK, ENERGY_DECAY_WORK = 0.05, 0.2, 0.5
    
    # --- HAPPINESS LOGIC ---
    HAPPINESS_DECAY_IDLE = 0.002
    HAPPINESS_DECAY_TRAIN = 0.015
    HAPPINESS_DECAY_WORK = 0.008
    HAPPINESS_DECAY_ANGRY = 0.02
    HAPPINESS_DECAY_NEGLECT = 0.01
    NEGLECT_THRESHOLD = 300 # 5 minutes
    HAPPINESS_THRESHOLD_SAD = 25.0

    ENERGY_THRESHOLD_TIRED, ENERGY_THRESHOLD_SLEEP = 15.0, 5.0
    XP_PER_TRAINING, COINS_PER_TRAINING = 25, 15
    PLAY_XP_REWARD = 10
    DANCE_XP_REWARD = 5
    
    # --- PROGRESSION ---
    BASE_XP_REQ = 100 # Base XP for lvl 2
    LEVEL_UP_REWARD_COINS = 50
    STAT_BOOST_PER_LEVEL = 20 # +20 to max stats per level

    # SHOP
    MEDICINE_HEAL_AMOUNT = 50
    
    SHOP_PRICES = {
        # Sweets
        "lollipop": 5, "toffee": 8, "gummy-bear": 10, "donut": 10, 
        "chocolate": 12, "candy-apple": 15, "croissant": 20,
        
        # Food
        "sandwich": 10, "fried-potatoes": 12, "rice": 15, "hot-dog": 15, 
        "salad": 20, "sushi": 30, "pasta": 35, "pizza": 40, "ramen": 50,
        
        # Fruits & Veg (Health)
        "blueberry": 1, "apple": 2, "tomato": 3, "banana": 3, "cucumber": 4, 
        "nuts": 5, "pomegranate": 6, "dragon-fruit": 9, "pumpkin": 12,

        # Toys & Gifts
        "ball": 30, "medicine": 50, "joystick": 60, "book": 30,
        "flowers": 25, "teddy-bear": 55, "sword-gift": 100, "crown": 250,
        "headphones": 150, "gem": 200, "magic-wand": 300, 
        "love-potion": 150, "smartphone": 500
    }
    
    FOOD_STATS = {
        "sandwich": 20, "hot-dog": 25, "sushi": 30, "fried-potatoes": 35, 
        "rice": 35, "salad": 15, "pizza": 45, "pasta": 50, "ramen": 75
    }
    
    SWEET_STATS = {
        "lollipop": 10, "toffee": 15, "gummy-bear": 20, "chocolate": 25, 
        "candy-apple": 30, "donut": 10, "croissant": 35
    }
    
    # {Item: (Hunger, Health)}
    HEALTH_FOOD_STATS = {
        "blueberry": (0, 1), "apple": (1, 1), "tomato": (2, 1), "banana": (4, 1),
        "cucumber": (1, 1), "nuts": (6, 3), "pomegranate": (1, 4),
        "dragon-fruit": (2, 3), "pumpkin": (3, 6)
    }
    
    GIFT_STATS = {
        "flowers": 25, "teddy-bear": 50, "sword-gift": 80, "crown": 100,
        "book": 20, "headphones": 40, "gem": 50, "magic-wand": 60,
        "love-potion": 100, "smartphone": 75
    }
    
    SHOP_UNLOCKS = {
        # Level 1
        "blueberry": 1, "apple": 1, "tomato": 1, "banana": 1, "sandwich": 1, "ball": 1, "medicine": 1, "book": 1,
        # Level 2
        "cucumber": 2, "nuts": 2, "hot-dog": 2, "rice": 2, "salad": 2, "lollipop": 2, "donut": 2,
        # Level 3
        "pomegranate": 3, "pumpkin": 3, "fried-potatoes": 3, "toffee": 3, "croissant": 3, "headphones": 3,
        # Level 4
        "dragon-fruit": 4, "sushi": 4, "pasta": 4, "gummy-bear": 4,
        # Level 5
        "pizza": 5, "ramen": 5, "chocolate": 5, "candy-apple": 5, "teddy-bear": 5, "gem": 5,
        # High Level
        "joystick": 7, "magic-wand": 7, "love-potion": 8, "sword-gift": 10, "smartphone": 10, "crown": 15
    }
    
    ACHIEVEMENTS = {
        "level_5": {"name": "П'ятірка!", "desc": "Досягти 5 рівня", "icon": "crown.png"},
        "level_10": {"name": "Ветеран", "desc": "Досягти 10 рівня", "icon": "crown.png"},
        "level_20": {"name": "Легенда", "desc": "Досягти 20 рівня", "icon": "crown.png"},
        
        "rich": {"name": "Мільйонер", "desc": "Накопичити 1000 монет", "icon": "crown.png"},
        "tycoon": {"name": "Магнат", "desc": "Накопичити 5000 монет", "icon": "crown.png"},
        
        "best_friend": {"name": "Найкращі друзі", "desc": "100% щастя", "icon": "flowers.png"},
        
        "gamer": {"name": "Геймер", "desc": "Зіграти в ігри 10 разів", "icon": "joystick.png"},
        "pro_gamer": {"name": "Кіберспортсмен", "desc": "Зіграти в ігри 50 разів", "icon": "joystick.png"},
        
        "worker": {"name": "Трудоголік", "desc": "Працювати 60 хв сумарно", "icon": "working.png"},
        "manager": {"name": "Менеджер", "desc": "Працювати 5 годин сумарно", "icon": "working.png"},
        
        "hoarder": {"name": "Колекціонер", "desc": "Мати 20 предметів в інвентарі", "icon": "ball.png"}
    }
    
    PLAY_ITEMS = ["ball", "joystick"]

    # MINI-GAMES
    MINIGAME_DURATION = 15 # seconds
    COIN_REWARD = 1

    import sys
    if getattr(sys, 'frozen', False):
        # Running as executable
        BASE_DIR = sys._MEIPASS # Assets embedded in temp folder
        ROOT_DIR = os.path.dirname(sys.executable) # Executable location for saves
    else:
        # Running from source
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ROOT_DIR = BASE_DIR

    ANIM_DIR = os.path.join(BASE_DIR, "assets", "animations")
    
    # Save data acts as persistent storage, so it goes to ROOT_DIR (next to exe)
    DATA_DIR = os.path.join(ROOT_DIR, "data")
    SAVE_PATH = os.path.join(DATA_DIR, "stats.json")
    
    UI_DIR = os.path.join(BASE_DIR, "assets", "ui", "emotes")
    ICONS_DIR = os.path.join(BASE_DIR, "assets", "ui", "icons")
    SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")
    
    SOUNDS = {
        "click": "click.wav",
        "eat": "eat.wav",
        "training": "training.wav",
        "arigato": "arigato.wav",
        "drag": "drag.wav",
        "angry": "angry.wav",
        "happy": "happy.wav",
        "sleep": "sleep.wav",
        "coin_game": "coin_game.wav",
        "quest": "quest.wav",
        "slots": "slots.wav"
    }