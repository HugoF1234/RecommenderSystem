"""
Script to load CSV data into database
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.database import Database
from src.data.loader import DataLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data_to_database():
    """Load recipes and reviews from CSV files into database"""
    
    # Initialize database
    db = Database(database_type="sqlite", sqlite_path="data/saveeat.db")
    
    # Initialize data loader
    loader = DataLoader(raw_data_path="data/raw")
    
    # Load recipes
    recipes_path = None
    possible_recipe_paths = [
        Path("data/raw/recipes_clean_full.csv"),
        Path("data/raw/recipes.csv"),
        Path("data/processed/recipes.csv"),
    ]
    
    for path in possible_recipe_paths:
        if path.exists():
            recipes_path = path
            break
    
    if recipes_path:
        logger.info(f"Loading recipes from {recipes_path}")
        try:
            db.load_recipes_from_csv(str(recipes_path))
            logger.info("Recipes loaded successfully!")
        except Exception as e:
            logger.error(f"Error loading recipes: {e}")
    else:
        logger.warning("Recipes CSV not found. Please ensure recipes CSV is in data/raw/")
    
    # Load reviews
    reviews_path = None
    possible_review_paths = [
        Path("data/raw/reviews_clean_full.csv"),
        Path("data/raw/reviews.csv"),
    ]
    
    for path in possible_review_paths:
        if path.exists():
            reviews_path = path
            break
    
    if reviews_path:
        logger.info(f"Loading reviews from {reviews_path}")
        try:
            db.load_reviews_from_csv(str(reviews_path))
            logger.info("Reviews loaded successfully!")
        except Exception as e:
            logger.error(f"Error loading reviews: {e}")
    else:
        logger.warning("Reviews CSV not found. Please ensure reviews CSV is in data/raw/")
    
    logger.info("Data loading complete!")


if __name__ == "__main__":
    load_data_to_database()

