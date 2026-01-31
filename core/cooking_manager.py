import logging
from config.settings import Settings

class CookingManager:
    def __init__(self, stats_manager):
        self.stats = stats_manager
        self.logger = logging.getLogger("CookingManager")

    def get_result(self, ingredients):
        """
        Takes a list of ingredient IDs and returns the resulting item ID.
        """
        if not ingredients:
            return None
            
        ing_set = frozenset(ingredients)
        
        # Check for exact matches in RECIPES
        for recipe_set, result in Settings.COOKING_RECIPES.items():
            if ing_set == recipe_set:
                return result
        
        # If any ingredients were provided but no recipe matched -> Burnt Food
        return "burnt_food"

    def can_cook_recipe(self, recipe_id):
        """Checks if the user has unlocked the recipe."""
        # Recipes are stored in stats under "unlocked_recipes" or similar
        unlocked = self.stats.data.get("unlocked_recipes", [])
        return recipe_id in unlocked

    def unlock_recipe(self, recipe_id):
        if "unlocked_recipes" not in self.stats.data:
            self.stats.data["unlocked_recipes"] = []
            
        if recipe_id not in self.stats.data["unlocked_recipes"]:
            self.stats.data["unlocked_recipes"].append(recipe_id)
            self.stats.save_stats()
            return True
        return False

    def perform_cooking(self, ingredients_list):
        """
        Consumes ingredients and returns the resulting item.
        """
        # 1. Verify availability
        for ing in ingredients_list:
            if self.stats.data["inventory"].get(ing, 0) <= 0:
                self.logger.warning(f"Missing ingredient for cooking: {ing}")
                return None

        # 2. Consume ingredients
        for ing in ingredients_list:
            self.stats.data["inventory"][ing] -= 1
            if self.stats.data["inventory"][ing] <= 0:
                del self.stats.data["inventory"][ing]

        # 3. Determine result
        result = self.get_result(ingredients_list)
        
        # 4. Add result to inventory
        if result:
            self.stats.add_item(result)
            self.stats.save_stats()
            
        return result
