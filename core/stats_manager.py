import json
import os
from config.settings import Settings

class StatsManager:
    def __init__(self):
        # Шлях до файлу беремо з глобальних налаштувань
        self.save_path = Settings.SAVE_PATH
        self.data = self.load_stats()

    def load_stats(self):
        """Завантажує статистику з JSON або створює нову з повним інвентарем"""
        
        # Дефолтні значення (початковий стан гри)
        default_stats = {
            "hunger": 100.0, 
            "energy": 100.0, 
            "health": 100.0,
            "xp": 0,
            "level": 1,
            "inventory": {
                "sandwich": 3,
                "hot-dog": 2,
                "sushi": 2,
                "fried-potatoes": 1,
                "pizza": 1,
                "pasta": 1,
                "lollipop": 5,
                "chocolate": 2,
                "toffee": 3,
                "gummy-bear": 2,
                "candy-apple": 1
                
            }
        }

        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Перевірка на наявність усіх ключів (для сумісності зі старими сейвами)
                    for key, value in default_stats.items():
                        if key not in data:
                            data[key] = value
                    
                    # Перевірка самого інвентарю (щоб додати нові види їжі, якщо їх не було)
                    for item, count in default_stats["inventory"].items():
                        if item not in data["inventory"]:
                            data["inventory"][item] = count
                            
                    return data
            except Exception as e:
                print(f"Помилка завантаження сейву: {e}")
        
        return default_stats

    def update(self):
        """Логіка метаболізму: викликається в кожному кадрі update_loop"""
        # Отримуємо швидкість зменшення показників з налаштувань
        decay = getattr(Settings, "STATS_DECAY_RATE", 0.005)
        
        # 1. Зменшення голоду та енергії
        self.data["hunger"] = max(0.0, self.data["hunger"] - decay)
        self.data["energy"] = max(0.0, self.data["energy"] - decay * 0.7)
        
        # 2. Логіка здоров'я (Health)
        # Якщо Асуна дуже голодна або втомлена - здоров'я падає
        if self.data["hunger"] < 15 or self.data["energy"] < 15:
            self.data["health"] = max(0.0, self.data["health"] - decay * 1.5)
        
        # Якщо вона сита (>60) та бадьора - здоров'я потроху відновлюється
        elif self.data["hunger"] > 60 and self.data["energy"] > 50:
            self.data["health"] = min(100.0, self.data["health"] + decay * 0.5)

    def use_item(self, item_id):
        """Витрачає один предмет з інвентарю. Повертає True, якщо успішно."""
        if self.data["inventory"].get(item_id, 0) > 0:
            self.data["inventory"][item_id] -= 1
            return True
        return False

    def add_xp(self, amount):
        """Додає досвід та обробляє Level Up"""
        self.data["xp"] += amount
        
        # Визначаємо, скільки XP треба для наступного рівня
        xp_needed = getattr(Settings, "LEVEL_UP_XP", 100)
        
        if self.data["xp"] >= xp_needed:
            self.data["xp"] = 0 # Скидаємо XP
            self.data["level"] += 1
            return True # Сигнал для Engine, що стався Level Up
        return False

    def save_stats(self):
        """Зберігає поточний стан у файл JSON"""
        try:
            # Створюємо папку, якщо її ще немає
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            with open(self.save_path, 'w', encoding='utf-8') as f:
                # indent=4 робить файл читабельним для людини
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Помилка збереження статистики: {e}")