"""
Script to load data into PostgreSQL database
Can be used locally or on Render
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.database import Database
from src.data.loader import DataLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_to_postgres(
    host: str = None,
    port: int = None,
    database: str = None,
    user: str = None,
    password: str = None
):
    """
    Load data into PostgreSQL database
    
    Args:
        host: PostgreSQL host (default: from env or localhost)
        port: PostgreSQL port (default: from env or 5432)
        database: Database name (default: from env or saveeat)
        user: Database user (default: from env or postgres)
        password: Database password (default: from env or empty)
    """
    
    # Priority 1: Parse DATABASE_URL if available (Render format)
    database_url = os.getenv("DATABASE_URL")
    if database_url and not host:
        try:
            from urllib.parse import urlparse
            db_url = urlparse(database_url)
            host = db_url.hostname
            port = db_url.port or 5432
            database = db_url.path[1:] if db_url.path else "saveeat"
            user = db_url.username
            password = db_url.password
            logger.info(f"Using DATABASE_URL: {host}:{port}/{database}")
        except Exception as e:
            logger.warning(f"Failed to parse DATABASE_URL: {e}")
    
    # Priority 2: Use provided arguments or environment variables
    host = host or os.getenv("POSTGRESQL_HOST") or os.getenv("DATABASE_HOST") or "localhost"
    port = port or int(os.getenv("POSTGRESQL_PORT", os.getenv("DATABASE_PORT", "5432")))
    database = database or os.getenv("POSTGRESQL_DATABASE") or os.getenv("DATABASE_NAME") or "saveeat"
    user = user or os.getenv("POSTGRESQL_USER") or os.getenv("DATABASE_USER") or "postgres"
    password = password or os.getenv("POSTGRESQL_PASSWORD") or os.getenv("DATABASE_PASSWORD") or ""
    
    logger.info(f"Connecting to PostgreSQL: {user}@{host}:{port}/{database}")
    
    # Initialize database with PostgreSQL
    db = Database(
        database_type="postgresql",
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
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
            count = db.load_recipes_from_csv(str(recipes_path))
            logger.info(f"Successfully loaded {count} recipes!")
        except Exception as e:
            logger.error(f"Error loading recipes: {e}")
            raise
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
            count = db.load_reviews_from_csv(str(reviews_path))
            logger.info(f"Successfully loaded {count} reviews!")
        except Exception as e:
            logger.error(f"Error loading reviews: {e}")
            raise
    else:
        logger.warning("Reviews CSV not found. Please ensure reviews CSV is in data/raw/")
    
    logger.info("Data loading complete!")
    
    # Verify data
    session = db.get_session()
    try:
        from src.api.database import Recipe, Review
        recipe_count = session.query(Recipe).count()
        review_count = session.query(Review).count()
        logger.info(f"Database now contains: {recipe_count} recipes, {review_count} reviews")
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load data into PostgreSQL")
    parser.add_argument("--host", type=str, help="PostgreSQL host")
    parser.add_argument("--port", type=int, help="PostgreSQL port")
    parser.add_argument("--database", type=str, help="Database name")
    parser.add_argument("--user", type=str, help="Database user")
    parser.add_argument("--password", type=str, help="Database password")
    
    args = parser.parse_args()
    
    load_to_postgres(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password
    )

