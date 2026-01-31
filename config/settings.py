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
    SCALE_FACTOR = 1.0
    DEFAULT_SPRITE_HEIGHT = 200    
    
    # Per-animation scale adjustments (1.0 = default 200px)
    # Tweak these numbers to make animations look uniform
    ANIMATION_SCALES = {
        "idle": 1.0, "walk_left": 1.0, "walk_right": 1.0,
        "eat": 1.0, "sleep": 1.0,
        "playing": 1.0, "working": 1.0, "scared": 1.0,
        "shy": 1.0, "angry": 1.0, "tired": 1.0, "training": 2.0,
        "drag": 1.0, "excited": 1.0, "dance": 1.0, "sing": 1.0, "sad": 1.0,
        "cooking": 1.0
    }
    
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
        
        # Food & Ingredients
        "sandwich": 15, "fried-potatoes": 12, "rice": 15, "hot-dog": 15, 
        "salad": 20, "sushi": 30, "pasta": 35, "pizza": 40, "ramen": 50,
        "meat": 15, "fish": 15, "shrimp": 20, "egg": 5, "cheese": 10, 
        "flour": 5, "milk": 8, "lettuce": 5, "tomato": 5,
        
        # Fruits & Veg (Health)
        "blueberry": 1, "apple": 2, "tomato": 3, "banana": 3, "cucumber": 4, 
        "nuts": 5, "pomegranate": 6, "dragon-fruit": 9, "pumpkin": 12,

        # Toys & Gifts
        "ball": 30, "medicine": 50, "joystick": 60, "book": 30,
        "flowers": 25, "teddy-bear": 55, "sword-gift": 100, "crown": 250,
        "headphones": 150, "gem": 200, "magic-wand": 300, 
        "love-potion": 150, "smartphone": 500,

        # Recipes
        "recipe_burger": 100, "recipe_sushi_set": 150, "recipe_cake": 200,
        "energy_drink": 30
    }
    
    # Basic food values
    FOOD_STATS = {
        "sandwich": 20.0, "fried-potatoes": 15.0, "rice": 10.0, "hot-dog": 25.0,
        "sushi": 35.0, "pasta": 40.0, "pizza": 45.0, "ramen": 55.0,
        "chocolate": 10.0, "energy_drink": 5.0,
        "burger": 60.0, "sushi_set": 50.0, "cake": 40.0, "salad": 30.0, 
        "burnt_food": 5.0,
        # Ingredients (can be eaten raw but low value)
        "meat": 5, "fish": 5, "shrimp": 5, "egg": 2, "cheese": 5, "flour": 1, "milk": 5, "lettuce": 5, "tomato": 5, "rice": 2
    }
    
    SWEET_STATS = {
        "lollipop": 10, "toffee": 15, "gummy-bear": 20, "chocolate": 25, 
        "candy-apple": 30, "donut": 10, "croissant": 35
    }
    
    # Healthy food that heals (+Hunger, +Health)
    HEALTH_FOOD_STATS = {
        "salad": (30, 5),
        "burnt_food": (5, -5), # Actually unhealthy
        "blueberry": (0, 1), "apple": (1, 1), "tomato": (2, 1), "banana": (4, 1),
        "cucumber": (1, 1), "nuts": (6, 3), "pomegranate": (1, 4),
        "dragon-fruit": (2, 3), "pumpkin": (3, 6), "medicine": (0, 50)
    }
    
    GIFT_STATS = {
        "flowers": 25, "teddy-bear": 50, "sword-gift": 80, "crown": 100,
        "book": 20, "headphones": 40, "gem": 50, "magic-wand": 60,
        "love-potion": 100, "smartphone": 75, "ball": 15, "joystick": 30
    }
    
    SHOP_UNLOCKS = {
        # Level 1
        "blueberry": 1, "apple": 1, "tomato": 1, "banana": 1, "sandwich": 1, "ball": 1, "medicine": 1, "book": 1,
        "meat": 1, "egg": 1, "flour": 1, "milk": 1, "lettuce": 1, "flowers": 1,
        # Level 2
        "cucumber": 2, "nuts": 2, "hot-dog": 2, "rice": 2, "salad": 2, "lollipop": 2, "donut": 2,
        "cheese": 2, "fish": 2, "recipe_burger": 2,
        # Level 3
        "pomegranate": 3, "pumpkin": 3, "fried-potatoes": 3, "toffee": 3, "croissant": 3, "headphones": 3,
        "shrimp": 3, "recipe_sushi_set": 3, "energy_drink": 3,
        # Level 4
        "dragon-fruit": 4, "sushi": 4, "pasta": 4, "gummy-bear": 4,
        "recipe_cake": 4,
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
    
    # Descriptions and Effects
    ITEM_DESC = {
        "sandwich": "Смачний сендвіч з соусом. (+20 Hunger)",
        "ball": "Червоний м'ячик для гри. (+20 Happiness)",
        "medicine": "Ліки від застуди. (+30 Health)",
        "chocolate": "Солодка плитка шоколаду. (+10 Hunger, +10 Happiness)",
        "energy_drink": "Заряд бадьорості! (+40 Energy, -5 Health)",
        "lollipop": "Смачний льодяник. (+10 Hunger, +10 Happiness)",
        "toffee": "М'яка іриска. (+15 Hunger, +10 Happiness)",
        "gummy-bear": "Ведмедик гаммі. (+20 Hunger, +15 Happiness)",
        "donut": "Доцент з глазур'ю. (+10 Hunger, +5 Happiness)",
        "candy-apple": "Яблуко в карамелі. (+30 Hunger, +20 Happiness)",
        "croissant": "Французький круасан. (+35 Hunger, +15 Happiness)",
        
        "fried-potatoes": "Смажена картопля. (+15 Hunger)",
        "rice": "Порція білого рису. (+10 Hunger)",
        "hot-dog": "Хот-дог з гірчицею. (+25 Hunger)",
        "sushi": "Класичні роли. (+35 Hunger, +5 Happiness)",
        "pasta": "Італійська паста. (+40 Hunger)",
        "pizza": "Гаряча піца! (+45 Hunger, +10 Happiness)",
        "ramen": "Автентичний рамен. (+55 Hunger, +10 Happiness)",

        "blueberry": "Свіжа лохина. (+1 Health)",
        "apple": "Стигле яблуко. (+1 Hunger, +1 Health)",
        "tomato": "Червоний томат. (+2 Hunger, +1 Health)",
        "banana": "Поживний банан. (+4 Hunger, +1 Health)",
        "cucumber": "Свіжий огірок. (+1 Hunger, +1 Health)",
        "nuts": "Мікс горіхів. (+6 Hunger, +3 Health)",
        "pomegranate": "Стиглий гранат. (+1 Hunger, +4 Health)",
        "dragon-fruit": "Екзотичний пітайя. (+2 Hunger, +3 Health)",
        "pumpkin": "Золотистий гарбуз. (+3 Hunger, +6 Health)",

        "joystick": "Ігрова консоль. (+60 Happiness)",
        "book": "Цікава книга. (+20 Happiness, +5 XP)",
        "flowers": "Букет квітів. (+25 Happiness)",
        "teddy-bear": "Плюшевий ведмедик. (+50 Happiness)",
        "sword-gift": "Декоративний меч. (+80 Happiness)",
        "crown": "Справжня корона! (+100 Happiness)",
        "headphones": "Музичні навушники. (+40 Happiness)",
        "gem": "Коштовний камінь. (+50 Happiness)",
        "magic-wand": "Магічна паличка. (+60 Happiness)",
        "love-potion": "Любовне зілля ❤️ (+100 Happiness)",
        "smartphone": "Сучасний смартфон. (+75 Happiness)",

        "meat": "Свіже м'ясо для кулінарії.",
        "fish": "Свіжа риба.",
        "shrimp": "Великі креветки.",
        "egg": "Куряче яйце.",
        "cheese": "Шматочок сиру.",
        "flour": "Пшеничне борошно.",
        "milk": "Свіже молоко.",
        "lettuce": "Лист салату.",
        "recipe_burger": "Рецепт приготування бургера.",
        "recipe_sushi_set": "Секрети японської кухні (Суші).",
        "recipe_cake": "Мистецтво випікання тортів.",
        "burger": "Домашній бургер. (+60 Hunger, +10 Happiness)",
        "sushi_set": "Набір суші. (+50 Hunger, +15 Happiness)",
        "cake": "Святковий торт! (+40 Hunger, +30 Happiness)",
        "salad": "Легкий салат. (+30 Hunger, +5 Health)",
        "burnt_food": "Щось пішло не так... 🤢 (+5 Hunger, -5 Health)"
    }

    # Cooking Logic
    # Returns the result item based on a set of ingredient IDs
    COOKING_RECIPES = {
        frozenset(["meat", "flour", "cheese"]): "burger",
        frozenset(["fish", "rice", "shrimp"]): "sushi_set",
        frozenset(["flour", "milk", "egg", "chocolate"]): "cake",
        frozenset(["lettuce", "tomato"]): "salad",
    }
    
    INGREDIENTS = ["meat", "fish", "shrimp", "egg", "cheese", "flour", "milk", "lettuce", "tomato", "rice"]
    PREPARED_FOODS = ["burger", "sushi_set", "cake", "salad", "burnt_food"]
    
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