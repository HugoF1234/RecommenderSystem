"""
Load data from database and create processed files for model training
This allows preprocessing without needing raw CSV files
"""

import pandas as pd
import pickle
import torch
from pathlib import Path
from typing import Dict, Optional
import logging
from sqlalchemy import create_engine
import yaml

from ..api.database import Database, Recipe, Review
from .preprocessing import DataPreprocessor
from .graph_builder import GraphBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data_from_db(
    db_path: str = "data/saveeat.db",
    database_type: str = "sqlite"
) -> Dict:
    """
    Load recipes and reviews from database
    
    Args:
        db_path: Path to database file (for SQLite) or connection string
        database_type: "sqlite" or "postgresql"
    
    Returns:
        Dictionary with 'recipes' and 'interactions' DataFrames
    """
    logger.info(f"Loading data from {database_type} database...")
    
    # Initialize database connection
    if database_type == "sqlite":
        db = Database(database_type="sqlite", sqlite_path=db_path)
    else:
        # PostgreSQL - parse connection string
        import os
        from urllib.parse import urlparse
        db_url = urlparse(os.getenv("DATABASE_URL", db_path))
        db = Database(
            database_type="postgresql",
            host=db_url.hostname,
            port=db_url.port or 5432,
            database=db_url.path[1:] if db_url.path else "saveeat",
            user=db_url.username,
            password=db_url.password
        )
    
    session = db.get_session()
    
    try:
        # Load recipes
        logger.info("Loading recipes from database...")
        recipes_query = session.query(
            Recipe.recipe_id,
            Recipe.name,
            Recipe.description,
            Recipe.ingredients_list,
            Recipe.steps_list,
            Recipe.image_url,
            Recipe.minutes,
            Recipe.n_steps,
            Recipe.n_ingredients,
            Recipe.nutrition,
            Recipe.submitted,
            Recipe.tags,
            Recipe.calories,
            Recipe.total_fat,
            Recipe.sugar,
            Recipe.sodium,
            Recipe.protein,
            Recipe.saturated_fat,
            Recipe.carbohydrates
        )
        
        recipes_df = pd.read_sql(recipes_query.statement, session.bind)
        logger.info(f"Loaded {len(recipes_df)} recipes")
        
        # Rename columns to match expected format
        recipes_df = recipes_df.rename(columns={
            "name": "Name",
            "description": "Description",
            "minutes": "prep_time"
        })
        
        # Load reviews (interactions)
        logger.info("Loading reviews from database...")
        reviews_query = session.query(
            Review.user_id,
            Review.recipe_id,
            Review.rating,
            Review.review,
            Review.date
        )
        
        reviews_df = pd.read_sql(reviews_query.statement, session.bind)
        logger.info(f"Loaded {len(reviews_df)} reviews")
        
        # Rename to match expected format
        reviews_df = reviews_df.rename(columns={
            "rating": "Rating"
        })
        
        # Create interactions DataFrame (expected format)
        interactions_df = reviews_df[["user_id", "recipe_id", "Rating"]].copy()
        interactions_df = interactions_df.rename(columns={
            "user_id": "user_id",
            "recipe_id": "recipe_id",
            "Rating": "rating"
        })
        
        return {
            "recipes": recipes_df,
            "interactions": interactions_df,
            "reviews": reviews_df
        }
        
    finally:
        session.close()


def preprocess_from_db(
    db_path: str = "data/saveeat.db",
    database_type: str = "sqlite",
    output_path: Optional[Path] = None,
    config_path: Optional[Path] = None
):
    """
    Complete preprocessing pipeline using database as source
    
    Args:
        db_path: Path to database file
        database_type: "sqlite" or "postgresql"
        output_path: Path to save processed files
        config_path: Path to config.yaml
    """
    if output_path is None:
        output_path = Path("data/processed")
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load config
    if config_path is None:
        config_path = Path("config/config.yaml")
    
    config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    
    dataset_config = config.get("dataset", {})
    preprocessor_config = {
        "min_user_interactions": dataset_config.get("min_user_interactions", 5),
        "min_recipe_ratings": dataset_config.get("min_recipe_ratings", 3),
        "train_ratio": dataset_config.get("train_ratio", 0.7),
        "val_ratio": dataset_config.get("val_ratio", 0.15),
        "test_ratio": dataset_config.get("test_ratio", 0.15)
    }
    
    # Load data from database
    data = load_data_from_db(db_path, database_type)
    
    # Preprocess
    logger.info("Starting preprocessing...")
    preprocessor = DataPreprocessor(**preprocessor_config)
    processed_data = preprocessor.process(
        data["interactions"],
        data["recipes"],
        save_path=output_path
    )
    
    # Build graph
    logger.info("Building graph...")
    graph_builder = GraphBuilder(embedding_dim=config.get("graph", {}).get("embedding_dim", 128))
    
    # Get train interactions for graph building (already mapped with user_idx and recipe_idx by preprocessor)
    train_interactions = processed_data["train"].copy()  # Make a copy to avoid modifying original
    processed_recipes = processed_data["recipes"].copy()  # Make a copy
    mappings = processed_data["mappings"]
    
    # The preprocessor already adds user_idx and recipe_idx to interactions, but let's verify
    logger.info(f"Train interactions columns: {train_interactions.columns.tolist()}")
    if "user_idx" not in train_interactions.columns:
        logger.warning("user_idx not found, creating it...")
        train_interactions["user_idx"] = train_interactions["user_id"].map(mappings["user_to_idx"])
    if "recipe_idx" not in train_interactions.columns:
        logger.warning("recipe_idx not found, creating it...")
        train_interactions["recipe_idx"] = train_interactions["recipe_id"].map(mappings["recipe_to_idx"])
    
    # Add recipe_idx to recipes DataFrame (needed for graph building)
    if "recipe_idx" not in processed_recipes.columns:
        logger.info("Adding recipe_idx to recipes DataFrame...")
        processed_recipes["recipe_idx"] = processed_recipes["recipe_id"].map(mappings["recipe_to_idx"])
    
    # Remove any NaN values (users/recipes not in mappings)
    train_interactions = train_interactions.dropna(subset=["user_idx", "recipe_idx"])
    processed_recipes = processed_recipes.dropna(subset=["recipe_idx"])
    
    graph_data = graph_builder.build_hetero_graph(
        train_interactions,
        processed_recipes,
        mappings,
        include_ingredients=True
    )
    
    # Save graph
    graph_path = output_path / "graph.pt"
    torch.save(graph_data, graph_path)
    logger.info(f"✅ Saved graph to {graph_path}")
    
    logger.info("✅ Preprocessing complete!")
    logger.info(f"   - {processed_data['stats']['n_users']} users")
    logger.info(f"   - {processed_data['stats']['n_recipes']} recipes")
    logger.info(f"   - Train: {len(processed_data['train'])} interactions")
    logger.info(f"   - Val: {len(processed_data['val'])} interactions")
    logger.info(f"   - Test: {len(processed_data['test'])} interactions")
    logger.info(f"   - Graph: {graph_data.num_nodes} nodes, {graph_data.num_edges} edges")
    
    return processed_data, graph_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess data from database")
    parser.add_argument("--db-path", type=str, default="data/saveeat.db", help="Database path")
    parser.add_argument("--db-type", type=str, choices=["sqlite", "postgresql"], default="sqlite", help="Database type")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Config file path")
    
    args = parser.parse_args()
    
    preprocess_from_db(
        db_path=args.db_path,
        database_type=args.db_type,
        output_path=Path(args.output),
        config_path=Path(args.config)
    )

