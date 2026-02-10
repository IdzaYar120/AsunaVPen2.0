import json
import os
import time
from datetime import datetime

class JournalManager:
    """Manages Asuna's diary, recording events and generating summaries."""
    def __init__(self, data_dir):
        self.log_path = os.path.join(data_dir, "journal.json")
        self.entries = self._load()

    def _load(self):
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save(self):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(self.entries, f, indent=4, ensure_ascii=False)

    def log_event(self, event_type, details=""):
        """Logs an event for the current day."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.entries:
            self.entries[today] = []
        
        self.entries[today].append({
            "time": datetime.now().strftime("%H:%M"),
            "type": event_type,
            "details": details
        })
        self.save()

    def get_summary_text(self, date_str):
        """Generates a narrative text for a specific date."""
        events = self.entries.get(date_str, [])
        if not events:
            return "Сьогодні був тихий день... Ми просто відпочивали разом. ✨"

        # Simple narrative generator
        actions = []
        for e in events:
            if e["type"] == "eat": actions.append("ми смачно поїли")
            elif e["type"] == "play": actions.append("ми весело грали з м'ячем")
            elif e["type"] == "train": actions.append("я старанно тренувалася")
            elif e["type"] == "work": actions.append("ми продуктивно попрацювали")
            elif e["type"] == "achievement": actions.append(f"я розблокувала нове досягнення: {e['details']}!")

        text = f"Любий щоденнику... Сьогодні {date_str}. \n\n"
        if actions:
            text += "Сьогодні був чудовий день! " + ", а ще ".join(list(set(actions))) + ". "
        
        text += "\n\nМені дуже подобається проводити час разом. Сподіваюся, завтра буде ще краще! ❤️"
        return text
