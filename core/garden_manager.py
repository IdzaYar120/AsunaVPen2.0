import time
import logging
from config.settings import Settings

logger = logging.getLogger(__name__)

class GardenManager:
    def __init__(self, stats_manager):
        self.stats = stats_manager
        # Ensure garden data exists
        if "garden" not in self.stats.data:
            self.stats.data["garden"] = [
                {"plant": None, "stage": 0, "water": 0.0, "last_update": 0},
                {"plant": None, "stage": 0, "water": 0.0, "last_update": 0},
                {"plant": None, "stage": 0, "water": 0.0, "last_update": 0},
                {"plant": None, "stage": 0, "water": 0.0, "last_update": 0}
            ]
            self.stats.save_stats()
            
    def get_pot(self, index):
        if 0 <= index < 4:
            return self.stats.data["garden"][index]
        return None

    def plant_seed(self, index, seed_id):
        """Plants a seed in the specified pot. Seed ID should be like 'seed_tomato'."""
        pot = self.get_pot(index)
        if not pot or pot["plant"]:
            return False # Pot occupied or invalid

        plant_type = seed_id.replace("seed_", "")
        if plant_type not in Settings.GIFT_STATS and plant_type not in Settings.GARDEN_PLANTS:
            # Check against Garden Plants config
            if plant_type not in Settings.GARDEN_PLANTS:
                logger.error(f"Unknown plant type: {plant_type}")
                return False
        
        # Deduct seed from inventory (handled by UI/Caller usually, but let's verify)
        # Assuming caller checks inventory.
        
        pot["plant"] = plant_type
        pot["stage"] = 1
        pot["water"] = 100.0 # Start full water
        pot["last_update"] = time.time()
        
        self.stats.save_stats()
        return True

    def water_pot(self, index):
        """Refills water to 100%."""
        pot = self.get_pot(index)
        if not pot or not pot["plant"]:
            return False
            
        pot["water"] = 100.0
        pot["last_update"] = time.time() # Reset update timer effectively
        self.stats.save_stats()
        return True

    def harvest(self, index):
        """Harvests the plant if ripe and not withered."""
        pot = self.get_pot(index)
        if not pot or not pot["plant"]:
            return None
            
        # Check if withered
        if pot["water"] <= 0:
            # Withered, maybe just clear it? Or specific withered harvest logic?
            # User said: "After harvesting you get these plants as items". 
            # Implies successful harvest. Withered usually means you lose it or need to revive.
            # Plan says: "If water == 0, plant becomes withered".
            # Let's allow clearing withered plant (no reward).
            pot["plant"] = None
            pot["stage"] = 0
            pot["water"] = 0.0
            self.stats.save_stats()
            return "withered" # Special code

        if pot["stage"] < 4:
            return None # Not ready

        plant_type = pot["plant"]
        reward_item = Settings.GARDEN_PLANTS.get(plant_type, {}).get("reward", plant_type)
        
        # Add to inventory
        inv = self.stats.data["inventory"]
        inv[reward_item] = inv.get(reward_item, 0) + 1
        
        # Clear pot
        pot["plant"] = None
        pot["stage"] = 0
        pot["water"] = 0.0
        
        self.stats.save_stats()
        return reward_item

    def update_growth(self):
        """Called periodically to update plant growth and water levels."""
        now = time.time()
        updated = False
        
        for pot in self.stats.data["garden"]:
            if not pot["plant"]:
                continue
                
            # Delta time
            dt = now - pot["last_update"]
            if dt < 1: continue # throttle
            
            # Reset delta (we process it now)
            pot["last_update"] = now
            updated = True
            
            # Configs
            plant_conf = Settings.GARDEN_PLANTS.get(pot["plant"], {})
            growth_mult = plant_conf.get("growth_mult", 1.0)
            water_mult = plant_conf.get("water_mult", 1.0)
            
            base_decay = getattr(Settings, "GARDEN_WATER_DECAY", 0.5)
            # Water Decay
            decay = base_decay * water_mult * dt
            
            if pot["water"] > 0:
                pot["water"] = max(0.0, pot["water"] - decay)
                
                # Growth (only if not withered)
                if pot["water"] > 0 and pot["stage"] < 4:
                    # Logic: We store fractional growth? 
                    # Simpler: Accumulate 'growth_progress' or just assume reliable updates?
                    # Let's add 'growth_progress' to state if not exists, or hack it into time.
                    # Hack: Check if enough time passed since 'stage_start'?
                    # Better: Add 'growth_progress' (0-100) to state.
                    
                    if "growth_progress" not in pot: pot["growth_progress"] = 0.0
                    
                    # Growth needed per stage
                    stage_time = getattr(Settings, "GARDEN_GROWTH_TIME", 60)
                    progress_per_sec = (100.0 / stage_time) * growth_mult
                    
                    pot["growth_progress"] += progress_per_sec * dt
                    
                    if pot["growth_progress"] >= 100.0:
                        pot["stage"] += 1
                        pot["growth_progress"] = 0.0 # Reset for next stage
                        
            else:
                # Withered state (water <= 0)
                # No growth.
                pass
                
        if updated:
            self.stats.save_stats()
