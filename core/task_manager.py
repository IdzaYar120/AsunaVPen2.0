import time, random
from datetime import datetime
from core.quest_data import QUEST_DB

class TaskManager:
    DAILY_LIMIT = 10 # Daily Quest Limit

    def __init__(self, stats_manager):
        self.stats = stats_manager
        
    def generate_random_quest(self):
        # Check active quest limit (max 3)
        active = self.stats.data.get("tasks", [])
        if len(active) >= 3: return None
        
        # Select new quest
        template = random.choice(QUEST_DB)
        
        # Avoid duplicates
        for t in active:
            if t["text"] == template["text"]: return None
            
        quest = {
            "id": self._generate_id(),
            "type": template["type"],
            "target": template["target"],
            "required_count": template["count"],
            "current_count": 0,
            "text": template["text"],
            "xp": template["xp"],
            "money": template["money"],
            "happiness": template.get("happiness", 10),
            "created_at": time.time()
        }
        
        self.stats.data["tasks"].append(quest)
        self.stats.save_stats()
        return quest

    def check_event(self, event_type, value=None):
        """
        Triggered by user actions.
        event_type: 'eat', 'work', 'click', 'train', 'buy'
        value: 'pizza', 25, 'pet', etc.
        """
        completed_quests = []
        active = self.stats.data.get("tasks", [])
        
        for quest in active:
            if quest["type"] == event_type:
                match = False
                
                # Match Logic
                if event_type == "work":
                    # Check if duration meets requirement
                    if value >= quest["target"]: match = True
                elif event_type == "train":
                    match = True # Any training
                elif event_type == "cook":
                    # value is item_id (e.g. "burger")
                    if quest["target"] == "any" and value != "burnt_food": match = True
                    elif quest["target"] == value: match = True
                elif str(quest["target"]) == str(value):
                    match = True
                    
                if match:
                    quest["current_count"] += 1
                    if quest["current_count"] >= quest["required_count"]:
                        completed_quests.append(quest)
        
        # Process completed
        rewards = []
        for q in completed_quests:
            rewards.append(self.complete_quest(q))
            
        if completed_quests:
            self.stats.save_stats()
            
        return rewards

    def complete_quest(self, quest):
        self.remove_task(quest["id"])
        
        # --- Daily Logic ---
        today_str = datetime.now().strftime("%Y-%m-%d")
        last_date = self.stats.data.get("last_task_date", "")
        
        if last_date != today_str:
            self.stats.data["daily_tasks_completed"] = 0
            self.stats.data["last_task_date"] = today_str
            
        self.stats.data["daily_tasks_completed"] += 1
        count = self.stats.data["daily_tasks_completed"]
        
        rewards = {
            "xp": quest["xp"],
            "money": quest["money"],
            "happiness": quest.get("happiness", 10),
            "text": quest["text"],
            "bonus_applied": False
        }
        
        # Daily Bonus (e.g. 5th task)
        if count == 5:
            rewards["money"] += 100
            rewards["xp"] += 50
            rewards["bonus_applied"] = True
            
        self.stats.save_stats()
        return rewards
        
    def remove_task(self, task_id):
        self.stats.data["tasks"] = [
            t for t in self.stats.data["tasks"] 
            if t["id"] != task_id
        ]
        self.stats.save_stats()
        
    def _generate_id(self):
        return int(time.time() * 100000) + random.randint(0, 999)
