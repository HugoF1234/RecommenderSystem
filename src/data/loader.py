"""
Data Loader for Food.com Dataset
Downloads and loads the Food.com Recipes and Interactions dataset
"""

import os
import pandas as pd
import zipfile
from pathlib import Path
from typing import Tuple, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Handles loading of the Food.com dataset from Kaggle
    """
    
    def __init__(self, raw_data_path: str = "data/raw"):
        """
        Initialize the DataLoader
        
        Args:
            raw_data_path: Path to store raw dataset files
        """
        self.raw_data_path = Path(raw_data_path)
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        
    def download_dataset(self, kaggle_dataset: str = None):
        """
        Download dataset from Kaggle (requires kaggle API credentials)
        
        Args:
            kaggle_dataset: Kaggle dataset identifier. If None, uses default from config.
        """
        # Default to cleaned dataset
        if kaggle_dataset is None:
            kaggle_dataset = "recsys-project-dataset-foodcom"  # Update with actual Kaggle identifier
        
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            
            api = KaggleApi()
            api.authenticate()
            
            logger.info(f"Downloading cleaned dataset {kaggle_dataset} from Kaggle...")
            logger.info("Looking for recipes_clean_full.csv and reviews_clean_full.csv")
            api.dataset_download_files(
                kaggle_dataset,
                path=str(self.raw_data_path),
                unzip=True
            )
            logger.info("Dataset downloaded successfully!")
            
        except Exception as e:
            logger.error(f"Failed to download from Kaggle: {e}")
            logger.info("Please download manually from Kaggle: 'RecSys project dataset Food.com'")
            logger.info("Ensure you download recipes_clean_full.csv and reviews_clean_full.csv")
            logger.info(f"Extract files to: {self.raw_data_path}")
    
    def load_interactions(self) -> pd.DataFrame:
        """
        Load user-recipe interactions from cleaned dataset
        
        Returns:
            DataFrame with columns: user_id, recipe_id, rating, date, review
        """
        interactions_path = None
        
        # Prioritize cleaned dataset files
        possible_paths = [
            self.raw_data_path / "reviews_clean_full.csv",  # Cleaned dataset (priority)
            self.raw_data_path / "reviews_clean_sample.csv",  # Sample if full not available
            self.raw_data_path / "interactions_train.csv",
            self.raw_data_path / "RAW_interactions.csv",
            self.raw_data_path / "interactions.csv",
            self.raw_data_path / "reviews.csv"  # Original Food.com dataset
        ]
        
        for path in possible_paths:
            if path.exists():
                interactions_path = path
                break
        
        if interactions_path is None:
            raise FileNotFoundError(
                f"Interactions file not found. Tried: {[str(p) for p in possible_paths]}\n"
                "Please download the cleaned dataset from Kaggle: 'RecSys project dataset Food.com'\n"
                "Ensure reviews_clean_full.csv is in the data/raw/ directory."
            )
        
        logger.info(f"Loading interactions from {interactions_path}")
        df = pd.read_csv(interactions_path)
        
        # Standardize column names based on file format
        if "reviews_clean" in str(interactions_path) or "reviews.csv" in str(interactions_path):
            # Food.com format: ReviewId, RecipeId, AuthorId, Rating, Review, DateSubmitted
            # Cleaned dataset may have slightly different column names
            column_mapping = {
                "RecipeId": "recipe_id",
                "recipe_id": "recipe_id",  # Already correct
                "AuthorId": "user_id",
                "author_id": "user_id",  # Alternative naming
                "user_id": "user_id",  # Already correct
                "Rating": "rating",
                "rating": "rating",  # Already correct
                "Review": "review",
                "review": "review",  # Already correct
                "DateSubmitted": "date",
                "date": "date",  # Already correct
                "date_submitted": "date"  # Alternative naming
            }
            # Apply mapping only for columns that exist
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns and old_col != new_col:
                    df = df.rename(columns={old_col: new_col})
        else:
            # Standard format mapping
            column_mapping = {
                "user_id": "user_id",
                "recipe_id": "recipe_id",
                "rating": "rating",
                "date": "date",
                "review": "review"
            }
            # Map columns if they exist
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
        
        # Ensure date column is datetime
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        logger.info(f"Loaded {len(df)} interactions from cleaned dataset")
        return df
    
    def load_recipes(self) -> pd.DataFrame:
        """
        Load recipe data from cleaned dataset
        
        Returns:
            DataFrame with recipe information (id, name, ingredients, steps, etc.)
        """
        recipes_path = None
        
        # Prioritize cleaned dataset files
        possible_paths = [
            self.raw_data_path / "recipes_clean_full.csv",  # Cleaned dataset (priority)
            self.raw_data_path / "recipes_clean_sample.csv",  # Sample if full not available
            self.raw_data_path / "recipes.csv",
            self.raw_data_path / "RAW_recipes.csv"
        ]
        
        for path in possible_paths:
            if path.exists():
                recipes_path = path
                break
        
        if recipes_path is None:
            raise FileNotFoundError(
                f"Recipes file not found. Tried: {[str(p) for p in possible_paths]}\n"
                "Please download the cleaned dataset from Kaggle: 'RecSys project dataset Food.com'\n"
                "Ensure recipes_clean_full.csv is in the data/raw/ directory."
            )
        
        logger.info(f"Loading recipes from {recipes_path}")
        df = pd.read_csv(recipes_path)
        
        # Standardize column names for Food.com format
        # Cleaned dataset may have different column naming
        if "RecipeId" in df.columns:
            df = df.rename(columns={"RecipeId": "recipe_id"})
        elif "recipe_id" in df.columns:
            # Already correct, no change needed
            pass
        elif "id" in df.columns:
            df = df.rename(columns={"id": "recipe_id"})
        
        logger.info(f"Loaded {len(df)} recipes from cleaned dataset")
        return df
    
    def load_all(self) -> Dict[str, pd.DataFrame]:
        """
        Load all dataset files
        
        Returns:
            Dictionary containing 'interactions' and 'recipes' DataFrames
        """
        return {
            "interactions": self.load_interactions(),
            "recipes": self.load_recipes()
        }

