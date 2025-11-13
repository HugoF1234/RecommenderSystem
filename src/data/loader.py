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
        
    def download_dataset(self, kaggle_dataset: str = "irkaal/foodcom-recipes-and-reviews"):
        """
        Download dataset from Kaggle (requires kaggle API credentials)
        
        Args:
            kaggle_dataset: Kaggle dataset identifier
        """
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            
            api = KaggleApi()
            api.authenticate()
            
            logger.info(f"Downloading dataset {kaggle_dataset} from Kaggle...")
            api.dataset_download_files(
                kaggle_dataset,
                path=str(self.raw_data_path),
                unzip=True
            )
            logger.info("Dataset downloaded successfully!")
            
        except Exception as e:
            logger.error(f"Failed to download from Kaggle: {e}")
            logger.info("Please download manually from: https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews")
            logger.info(f"Extract files to: {self.raw_data_path}")
    
    def load_interactions(self) -> pd.DataFrame:
        """
        Load user-recipe interactions
        
        Returns:
            DataFrame with columns: user_id, recipe_id, rating, date, review
        """
        interactions_path = None
        
        # Try different possible file names
        possible_paths = [
            self.raw_data_path / "interactions_train.csv",
            self.raw_data_path / "RAW_interactions.csv",
            self.raw_data_path / "interactions.csv",
            self.raw_data_path / "reviews.csv"  # Food.com dataset uses reviews.csv
        ]
        
        for path in possible_paths:
            if path.exists():
                interactions_path = path
                break
        
        if interactions_path is None:
            raise FileNotFoundError(
                f"Interactions file not found. Tried: {[str(p) for p in possible_paths]}\n"
                "Please download the dataset from Kaggle."
            )
        
        logger.info(f"Loading interactions from {interactions_path}")
        df = pd.read_csv(interactions_path)
        
        # Standardize column names based on file format
        if "reviews.csv" in str(interactions_path):
            # Food.com format: ReviewId, RecipeId, AuthorId, Rating, Review, DateSubmitted
            column_mapping = {
                "RecipeId": "recipe_id",
                "AuthorId": "user_id",
                "Rating": "rating",
                "Review": "review",
                "DateSubmitted": "date"
            }
            df = df.rename(columns=column_mapping)
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
        
        logger.info(f"Loaded {len(df)} interactions")
        return df
    
    def load_recipes(self) -> pd.DataFrame:
        """
        Load recipe data
        
        Returns:
            DataFrame with recipe information (id, name, ingredients, steps, etc.)
        """
        recipes_path = None
        
        # Try different possible file names
        possible_paths = [
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
                "Please download the dataset from Kaggle."
            )
        
        logger.info(f"Loading recipes from {recipes_path}")
        df = pd.read_csv(recipes_path)
        
        # Standardize column names for Food.com format
        if "RecipeId" in df.columns:
            df = df.rename(columns={"RecipeId": "recipe_id"})
        elif "id" in df.columns:
            df = df.rename(columns={"id": "recipe_id"})
        
        logger.info(f"Loaded {len(df)} recipes")
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

