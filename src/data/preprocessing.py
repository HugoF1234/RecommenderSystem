"""
Data Preprocessing for Save Eat
Cleans and prepares data for model training
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, List, Optional
import logging
import pickle
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Preprocesses raw data for model training
    Filters users and recipes, creates features, and splits data
    """
    
    def __init__(
        self,
        min_user_interactions: int = 5,
        min_recipe_ratings: int = 3,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ):
        """
        Initialize preprocessor
        
        Args:
            min_user_interactions: Minimum interactions per user
            min_recipe_ratings: Minimum ratings per recipe
            train_ratio: Training set proportion
            val_ratio: Validation set proportion
            test_ratio: Test set proportion
        """
        self.min_user_interactions = min_user_interactions
        self.min_recipe_ratings = min_recipe_ratings
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
            "Ratios must sum to 1.0"
    
    def filter_data(
        self,
        interactions: pd.DataFrame,
        recipes: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Filter users and recipes based on minimum activity
        
        Args:
            interactions: User-recipe interactions
            recipes: Recipe data
            
        Returns:
            Filtered interactions and recipes DataFrames
        """
        logger.info(f"Original data: {len(interactions)} interactions, {len(recipes)} recipes")
        
        # Filter users with minimum interactions
        user_counts = interactions["user_id"].value_counts()
        valid_users = user_counts[user_counts >= self.min_user_interactions].index
        interactions = interactions[interactions["user_id"].isin(valid_users)]
        logger.info(f"After user filtering: {len(interactions)} interactions")
        
        # Filter recipes with minimum ratings
        recipe_counts = interactions["recipe_id"].value_counts()
        valid_recipes = recipe_counts[recipe_counts >= self.min_recipe_ratings].index
        interactions = interactions[interactions["recipe_id"].isin(valid_recipes)]
        recipes = recipes[recipes["recipe_id"].isin(valid_recipes)]
        logger.info(f"After recipe filtering: {len(interactions)} interactions, {len(recipes)} recipes")
        
        return interactions, recipes
    
    def extract_ingredients(self, recipes: pd.DataFrame) -> pd.DataFrame:
        """
        Extract and parse ingredients from recipes
        
        Args:
            recipes: Recipe DataFrame
            
        Returns:
            Recipes DataFrame with parsed ingredients
        """
        recipes = recipes.copy()
        
        # Parse ingredients - try different column names
        if "RecipeIngredientParts" in recipes.columns:
            # Food.com format: c("ingredient1", "ingredient2", ...)
            def parse_r_list(x):
                if pd.isna(x) or x == "":
                    return []
                if isinstance(x, str):
                    # Remove c( and ) and quotes
                    x = x.strip()
                    if x.startswith("c("):
                        x = x[2:]
                    if x.endswith(")"):
                        x = x[:-1]
                    # Split by quotes and filter
                    import re
                    ingredients = re.findall(r'"([^"]+)"', x)
                    return ingredients if ingredients else []
                elif isinstance(x, list):
                    return x
                return []
            
            recipes["ingredients_list"] = recipes["RecipeIngredientParts"].apply(parse_r_list)
        elif "ingredients" in recipes.columns:
            # Standard format: string representation of list
            recipes["ingredients_list"] = recipes["ingredients"].apply(
                lambda x: eval(x) if isinstance(x, str) else x if isinstance(x, list) else []
            )
        else:
            recipes["ingredients_list"] = [[]] * len(recipes)
        
        return recipes
    
    def create_features(self, recipes: pd.DataFrame) -> pd.DataFrame:
        """
        Create additional features from recipe data
        
        Args:
            recipes: Recipe DataFrame
            
        Returns:
            Recipes DataFrame with additional features
        """
        recipes = recipes.copy()
        
        # Extract preparation time if available
        if "PrepTime" in recipes.columns or "TotalTime" in recipes.columns:
            # Food.com uses ISO 8601 duration format (PT45M = 45 minutes)
            def parse_iso_duration(x):
                if pd.isna(x) or x == "":
                    return 0
                if isinstance(x, str):
                    import re
                    # Extract minutes: PT45M -> 45, PT1H30M -> 90
                    hours = re.findall(r'(\d+)H', x)
                    minutes = re.findall(r'(\d+)M', x)
                    total_minutes = (int(hours[0]) * 60 if hours else 0) + (int(minutes[0]) if minutes else 0)
                    return total_minutes if total_minutes > 0 else 0
                return 0
            
            if "TotalTime" in recipes.columns:
                recipes["prep_time"] = recipes["TotalTime"].apply(parse_iso_duration)
            elif "PrepTime" in recipes.columns:
                recipes["prep_time"] = recipes["PrepTime"].apply(parse_iso_duration)
        elif "minutes" in recipes.columns:
            recipes["prep_time"] = recipes["minutes"].fillna(0).astype(int)
        else:
            recipes["prep_time"] = 0
        
        # Extract nutrition information if available
        nutrition_cols = ["Calories", "FatContent", "SugarContent", "SodiumContent", "ProteinContent", 
                         "SaturatedFatContent", "CarbohydrateContent"]
        standard_nutrition = ["calories", "total_fat", "sugar", "sodium", "protein", 
                             "saturated_fat", "carbohydrates"]
        
        # Map Food.com nutrition columns to standard names
        for food_col, std_col in zip(nutrition_cols, standard_nutrition):
            if food_col in recipes.columns:
                recipes[std_col] = pd.to_numeric(recipes[food_col], errors="coerce").fillna(0)
            elif std_col not in recipes.columns:
                recipes[std_col] = 0
        
        # Create text features
        text_cols = []
        if "Name" in recipes.columns:
            recipes["name"] = recipes["Name"].fillna("")
            text_cols.append("name")
        elif "name" in recipes.columns:
            text_cols.append("name")
        
        if "Description" in recipes.columns:
            recipes["description"] = recipes["Description"].fillna("")
            text_cols.append("description")
        elif "description" in recipes.columns:
            text_cols.append("description")
        
        # Extract and parse images if available
        if "Images" in recipes.columns:
            def parse_r_list_images(x):
                if pd.isna(x) or x == "":
                    return []
                if isinstance(x, str):
                    x = x.strip()
                    if x.startswith("c("):
                        x = x[2:]
                    if x.endswith(")"):
                        x = x[:-1]
                    import re
                    # Extract URLs from the R-style list
                    urls = re.findall(r'"(https?://[^"]+)"', x)
                    return urls if urls else []
                elif isinstance(x, list):
                    return x
                return []
            
            recipes["images_list"] = recipes["Images"].apply(parse_r_list_images)
            # Set first image as primary image
            recipes["image_url"] = recipes["images_list"].apply(
                lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None
            )
        elif "image" in recipes.columns or "image_url" in recipes.columns:
            col_name = "image" if "image" in recipes.columns else "image_url"
            recipes["image_url"] = recipes[col_name].fillna("")
            recipes["images_list"] = recipes["image_url"].apply(lambda x: [x] if x else [])
        else:
            recipes["image_url"] = None
            recipes["images_list"] = recipes.apply(lambda x: [], axis=1)
        
        if "RecipeInstructions" in recipes.columns:
            # Food.com format: c("step1", "step2", ...)
            def parse_r_list_steps(x):
                if pd.isna(x) or x == "":
                    return []
                if isinstance(x, str):
                    x = x.strip()
                    if x.startswith("c("):
                        x = x[2:]
                    if x.endswith(")"):
                        x = x[:-1]
                    import re
                    steps = re.findall(r'"([^"]+)"', x)
                    return steps if steps else []
                elif isinstance(x, list):
                    return x
                return []
            
            recipes["steps_list"] = recipes["RecipeInstructions"].apply(parse_r_list_steps)
            recipes["steps_text"] = recipes["steps_list"].apply(
                lambda x: " ".join(str(s) for s in x) if isinstance(x, list) and len(x) > 0 else ""
            )
            text_cols.append("steps_text")
        elif "steps" in recipes.columns:
            # Standard format
            recipes["steps_list"] = recipes["steps"].apply(
                lambda x: eval(x) if isinstance(x, str) else x if isinstance(x, list) else []
            )
            recipes["steps_text"] = recipes["steps_list"].apply(
                lambda x: " ".join(str(s) for s in x) if isinstance(x, list) else ""
            )
            text_cols.append("steps_text")
        
        recipes["combined_text"] = recipes[text_cols].fillna("").agg(" ".join, axis=1)
        
        return recipes
    
    def split_data(
        self,
        interactions: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split interactions into train/val/test sets chronologically
        
        Args:
            interactions: Interactions DataFrame with 'date' column
            
        Returns:
            Train, validation, and test DataFrames
        """
        # Sort by date
        if "date" in interactions.columns:
            interactions = interactions.sort_values("date").reset_index(drop=True)
        else:
            interactions = interactions.reset_index(drop=True)
        
        n_total = len(interactions)
        n_train = int(n_total * self.train_ratio)
        n_val = int(n_total * self.val_ratio)
        
        train = interactions.iloc[:n_train].copy()
        val = interactions.iloc[n_train:n_train + n_val].copy()
        test = interactions.iloc[n_train + n_val:].copy()
        
        logger.info(f"Split: Train={len(train)}, Val={len(val)}, Test={len(test)}")
        
        return train, val, test
    
    def create_user_recipe_mappings(
        self,
        interactions: pd.DataFrame,
        recipes: pd.DataFrame
    ) -> Dict[str, Dict[int, int]]:
        """
        Create mappings from original IDs to sequential indices
        
        Args:
            interactions: Interactions DataFrame
            recipes: Recipes DataFrame
            
        Returns:
            Dictionary with mappings for users and recipes
        """
        unique_users = sorted(interactions["user_id"].unique())
        unique_recipes = sorted(recipes["recipe_id"].unique())
        
        user_to_idx = {user_id: idx for idx, user_id in enumerate(unique_users)}
        recipe_to_idx = {recipe_id: idx for idx, recipe_id in enumerate(unique_recipes)}
        
        idx_to_user = {idx: user_id for user_id, idx in user_to_idx.items()}
        idx_to_recipe = {idx: recipe_id for recipe_id, idx in recipe_to_idx.items()}
        
        return {
            "user_to_idx": user_to_idx,
            "recipe_to_idx": recipe_to_idx,
            "idx_to_user": idx_to_user,
            "idx_to_recipe": idx_to_recipe
        }
    
    def process(
        self,
        interactions: pd.DataFrame,
        recipes: pd.DataFrame,
        save_path: Optional[Path] = None
    ) -> Dict:
        """
        Complete preprocessing pipeline
        
        Args:
            interactions: Raw interactions DataFrame
            recipes: Raw recipes DataFrame
            save_path: Optional path to save processed data
            
        Returns:
            Dictionary with all processed data
        """
        logger.info("Starting preprocessing pipeline...")
        
        # Filter data
        interactions, recipes = self.filter_data(interactions, recipes)
        
        # Extract ingredients
        recipes = self.extract_ingredients(recipes)
        
        # Create features
        recipes = self.create_features(recipes)
        
        # Split data
        train, val, test = self.split_data(interactions)
        
        # Create mappings
        mappings = self.create_user_recipe_mappings(interactions, recipes)
        
        # Create mapped interactions (using sequential indices)
        train_mapped = train.copy()
        train_mapped["user_idx"] = train_mapped["user_id"].map(mappings["user_to_idx"])
        train_mapped["recipe_idx"] = train_mapped["recipe_id"].map(mappings["recipe_to_idx"])
        
        val_mapped = val.copy()
        val_mapped["user_idx"] = val_mapped["user_id"].map(mappings["user_to_idx"])
        val_mapped["recipe_idx"] = val_mapped["recipe_id"].map(mappings["recipe_to_idx"])
        
        test_mapped = test.copy()
        test_mapped["user_idx"] = test_mapped["user_id"].map(mappings["user_to_idx"])
        test_mapped["recipe_idx"] = test_mapped["recipe_id"].map(mappings["recipe_to_idx"])
        
        processed_data = {
            "train": train_mapped,
            "val": val_mapped,
            "test": test_mapped,
            "recipes": recipes,
            "mappings": mappings,
            "stats": {
                "n_users": len(mappings["user_to_idx"]),
                "n_recipes": len(mappings["recipe_to_idx"]),
                "n_interactions": len(interactions)
            }
        }
        
        if save_path:
            save_path = Path(save_path)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Save DataFrames
            processed_data["train"].to_csv(save_path / "train.csv", index=False)
            processed_data["val"].to_csv(save_path / "val.csv", index=False)
            processed_data["test"].to_csv(save_path / "test.csv", index=False)
            
            # Save recipes - convert lists to string representation for CSV
            recipes_to_save = processed_data["recipes"].copy()
            for col in ["ingredients_list", "steps_list", "images_list"]:
                if col in recipes_to_save.columns:
                    recipes_to_save[col] = recipes_to_save[col].apply(
                        lambda x: str(x) if isinstance(x, list) else x
                    )
            recipes_to_save.to_csv(save_path / "recipes.csv", index=False)
            
            # Save mappings
            with open(save_path / "mappings.pkl", "wb") as f:
                pickle.dump(mappings, f)
            
            # Save stats
            with open(save_path / "stats.json", "w") as f:
                json.dump(processed_data["stats"], f, indent=2)
            
            logger.info(f"Processed data saved to {save_path}")
        
        logger.info("Preprocessing complete!")
        return processed_data

