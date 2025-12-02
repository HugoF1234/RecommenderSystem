"""
Database module for Save Eat
Manages PostgreSQL/SQLite database for interactions
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from typing import Optional, Dict, List
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class Recipe(Base):
    """
    Recipe table for storing recipe data
    """
    __tablename__ = "recipes"
    
    recipe_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    ingredients_list = Column(JSON, nullable=True)  # List of ingredients as JSON
    steps = Column(Text, nullable=True)
    minutes = Column(Float, nullable=True)  # Preparation time in minutes
    n_steps = Column(Integer, nullable=True)
    n_ingredients = Column(Integer, nullable=True)
    nutrition = Column(JSON, nullable=True)  # Nutrition info as JSON
    submitted = Column(DateTime, nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags as JSON
    
    # Additional fields
    calories = Column(Float, nullable=True)
    total_fat = Column(Float, nullable=True)
    sugar = Column(Float, nullable=True)
    sodium = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    saturated_fat = Column(Float, nullable=True)
    carbohydrates = Column(Float, nullable=True)


class Review(Base):
    """
    Review table for storing user reviews/ratings
    """
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    recipe_id = Column(Integer, index=True, nullable=False)
    rating = Column(Float, nullable=True)
    review = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)
    
    # Index for faster queries
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class Interaction(Base):
    """
    Interaction table for logging user-recipe interactions
    """
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    recipe_id = Column(Integer, index=True)
    rating = Column(Float, nullable=True)
    review = Column(Text, nullable=True)
    interaction_type = Column(String, default="view")  # view, click, like, rate
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Contextual information
    available_ingredients = Column(Text, nullable=True)  # JSON string
    session_id = Column(String, nullable=True)


class Database:
    """
    Database manager for Save Eat
    """
    
    def __init__(self, database_type: str = "sqlite", **kwargs):
        """
        Initialize database
        
        Args:
            database_type: "sqlite" or "postgresql"
            **kwargs: Database connection parameters
        """
        self.database_type = database_type
        
        if database_type == "sqlite":
            db_path = kwargs.get("sqlite_path", "data/saveeat.db")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            database_url = f"sqlite:///{db_path}"
        elif database_type == "postgresql":
            host = kwargs.get("host", "localhost")
            port = kwargs.get("port", 5432)
            database = kwargs.get("database", "saveeat")
            user = kwargs.get("user", "postgres")
            password = kwargs.get("password", "")
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError(f"Unsupported database type: {database_type}")
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        logger.info(f"Database initialized: {database_type}")
    
    def get_session(self) -> Session:
        """
        Get database session
        
        Returns:
            Database session
        """
        return self.SessionLocal()
    
    def log_interaction(
        self,
        user_id: int,
        recipe_id: int,
        interaction_type: str = "view",
        rating: Optional[float] = None,
        review: Optional[str] = None,
        available_ingredients: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ):
        """
        Log a user-recipe interaction
        
        Args:
            user_id: User ID
            recipe_id: Recipe ID
            interaction_type: Type of interaction (view, click, like, rate)
            rating: Rating if available
            review: Review text if available
            available_ingredients: List of available ingredients
            session_id: Session identifier
        """
        session = self.get_session()
        try:
            import json
            
            interaction = Interaction(
                user_id=user_id,
                recipe_id=recipe_id,
                interaction_type=interaction_type,
                rating=rating,
                review=review,
                available_ingredients=json.dumps(available_ingredients) if available_ingredients else None,
                session_id=session_id,
                timestamp=datetime.utcnow()
            )
            
            session.add(interaction)
            session.commit()
            logger.info(f"Logged interaction: user={user_id}, recipe={recipe_id}, type={interaction_type}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log interaction: {e}")
            raise
        finally:
            session.close()
    
    def get_user_interactions(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get user's interaction history
        
        Args:
            user_id: User ID
            limit: Maximum number of interactions to return
            
        Returns:
            List of interaction dictionaries
        """
        session = self.get_session()
        try:
            interactions = session.query(Interaction).filter(
                Interaction.user_id == user_id
            ).order_by(
                Interaction.timestamp.desc()
            ).limit(limit).all()
            
            result = []
            import json
            for interaction in interactions:
                result.append({
                    "id": interaction.id,
                    "user_id": interaction.user_id,
                    "recipe_id": interaction.recipe_id,
                    "rating": interaction.rating,
                    "review": interaction.review,
                    "interaction_type": interaction.interaction_type,
                    "timestamp": interaction.timestamp.isoformat(),
                    "available_ingredients": json.loads(interaction.available_ingredients) if interaction.available_ingredients else None,
                    "session_id": interaction.session_id
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user interactions: {e}")
            return []
        finally:
            session.close()
    
    def load_recipes_from_csv(self, csv_path: str, batch_size: int = 1000):
        """
        Load recipes from CSV file into database
        
        Args:
            csv_path: Path to recipes CSV file
            batch_size: Number of recipes to insert per batch
        """
        import pandas as pd
        import ast
        from pathlib import Path
        
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"Recipes CSV not found: {csv_path}")
        
        logger.info(f"Loading recipes from {csv_path}")
        session = self.get_session()
        
        try:
            # Check if recipes already exist
            existing_count = session.query(Recipe).count()
            if existing_count > 0:
                logger.info(f"Recipes table already has {existing_count} recipes. Skipping load.")
                return existing_count
            
            df = pd.read_csv(csv_path)
            total_recipes = len(df)
            logger.info(f"Loading {total_recipes} recipes...")
            
            # Standardize column names
            if "RecipeId" in df.columns:
                df = df.rename(columns={"RecipeId": "recipe_id"})
            if "id" in df.columns and "recipe_id" not in df.columns:
                df = df.rename(columns={"id": "recipe_id"})
            
            recipes_added = 0
            for i in range(0, total_recipes, batch_size):
                batch = df.iloc[i:i+batch_size]
                recipes_batch = []
                
                for _, row in batch.iterrows():
                    try:
                        # Parse ingredients_list
                        ingredients_list = None
                        if "ingredients_list" in row and pd.notna(row["ingredients_list"]):
                            try:
                                ingredients_list = ast.literal_eval(str(row["ingredients_list"]))
                            except:
                                ingredients_list = None
                        elif "ingredients" in row and pd.notna(row["ingredients"]):
                            try:
                                ingredients_list = ast.literal_eval(str(row["ingredients"]))
                            except:
                                ingredients_list = None
                        
                        # Parse nutrition
                        nutrition = None
                        if "nutrition" in row and pd.notna(row["nutrition"]):
                            try:
                                nutrition = ast.literal_eval(str(row["nutrition"]))
                            except:
                                nutrition = None
                        
                        # Parse tags
                        tags = None
                        if "tags" in row and pd.notna(row["tags"]):
                            try:
                                tags = ast.literal_eval(str(row["tags"]))
                            except:
                                tags = None
                        
                        recipe = Recipe(
                            recipe_id=int(row["recipe_id"]) if pd.notna(row.get("recipe_id")) else None,
                            name=str(row.get("name", "")) if pd.notna(row.get("name")) else "",
                            description=str(row.get("description", "")) if pd.notna(row.get("description")) else None,
                            ingredients_list=ingredients_list,
                            steps=str(row.get("steps", "")) if pd.notna(row.get("steps")) else None,
                            minutes=float(row["minutes"]) if pd.notna(row.get("minutes")) else None,
                            n_steps=int(row["n_steps"]) if pd.notna(row.get("n_steps")) else None,
                            n_ingredients=int(row["n_ingredients"]) if pd.notna(row.get("n_ingredients")) else None,
                            nutrition=nutrition,
                            tags=tags,
                            calories=float(row["calories"]) if pd.notna(row.get("calories")) else None,
                            total_fat=float(row["total_fat"]) if pd.notna(row.get("total_fat")) else None,
                            sugar=float(row["sugar"]) if pd.notna(row.get("sugar")) else None,
                            sodium=float(row["sodium"]) if pd.notna(row.get("sodium")) else None,
                            protein=float(row["protein"]) if pd.notna(row.get("protein")) else None,
                            saturated_fat=float(row["saturated_fat"]) if pd.notna(row.get("saturated_fat")) else None,
                            carbohydrates=float(row["carbohydrates"]) if pd.notna(row.get("carbohydrates")) else None,
                        )
                        
                        recipes_batch.append(recipe)
                    except Exception as e:
                        logger.warning(f"Error processing recipe row: {e}")
                        continue
                
                session.bulk_save_objects(recipes_batch)
                session.commit()
                recipes_added += len(recipes_batch)
                logger.info(f"Loaded {recipes_added}/{total_recipes} recipes...")
            
            logger.info(f"Successfully loaded {recipes_added} recipes into database")
            return recipes_added
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to load recipes: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def load_reviews_from_csv(self, csv_path: str, batch_size: int = 1000):
        """
        Load reviews from CSV file into database
        
        Args:
            csv_path: Path to reviews CSV file
            batch_size: Number of reviews to insert per batch
        """
        import pandas as pd
        from datetime import datetime
        
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"Reviews CSV not found: {csv_path}")
        
        logger.info(f"Loading reviews from {csv_path}")
        session = self.get_session()
        
        try:
            # Check if reviews already exist
            existing_count = session.query(Review).count()
            if existing_count > 0:
                logger.info(f"Reviews table already has {existing_count} reviews. Skipping load.")
                return existing_count
            
            df = pd.read_csv(csv_path)
            total_reviews = len(df)
            logger.info(f"Loading {total_reviews} reviews...")
            
            # Standardize column names
            if "RecipeId" in df.columns:
                df = df.rename(columns={"RecipeId": "recipe_id"})
            if "AuthorId" in df.columns:
                df = df.rename(columns={"AuthorId": "user_id"})
            if "DateSubmitted" in df.columns:
                df = df.rename(columns={"DateSubmitted": "date"})
            
            reviews_added = 0
            for i in range(0, total_reviews, batch_size):
                batch = df.iloc[i:i+batch_size]
                reviews_batch = []
                
                for _, row in batch.iterrows():
                    try:
                        # Parse date
                        date_obj = None
                        if pd.notna(row.get("date")):
                            try:
                                date_obj = pd.to_datetime(row["date"])
                            except:
                                date_obj = None
                        
                        review = Review(
                            user_id=int(row["user_id"]) if pd.notna(row.get("user_id")) else None,
                            recipe_id=int(row["recipe_id"]) if pd.notna(row.get("recipe_id")) else None,
                            rating=float(row["rating"]) if pd.notna(row.get("rating")) else None,
                            review=str(row.get("review", "")) if pd.notna(row.get("review")) else None,
                            date=date_obj
                        )
                        
                        reviews_batch.append(review)
                    except Exception as e:
                        logger.warning(f"Error processing review row: {e}")
                        continue
                
                session.bulk_save_objects(reviews_batch)
                session.commit()
                reviews_added += len(reviews_batch)
                if reviews_added % 10000 == 0:
                    logger.info(f"Loaded {reviews_added}/{total_reviews} reviews...")
            
            logger.info(f"Successfully loaded {reviews_added} reviews into database")
            return reviews_added
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to load reviews: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def get_all_ingredients(self, limit: int = 500) -> List[str]:
        """
        Get all unique ingredients from recipes in database
        
        Args:
            limit: Maximum number of ingredients to return
            
        Returns:
            List of unique ingredients
        """
        session = self.get_session()
        try:
            recipes = session.query(Recipe).filter(
                Recipe.ingredients_list.isnot(None)
            ).all()
            
            all_ingredients = set()
            ingredient_counts = {}
            
            for recipe in recipes:
                if recipe.ingredients_list:
                    for ing in recipe.ingredients_list:
                        if isinstance(ing, str):
                            ing_clean = ing.strip().lower()
                            if ing_clean and len(ing_clean) > 1:
                                all_ingredients.add(ing_clean)
                                ingredient_counts[ing_clean] = ingredient_counts.get(ing_clean, 0) + 1
            
            # Sort by frequency (most common first) then alphabetically
            sorted_ingredients = sorted(
                list(all_ingredients),
                key=lambda x: (-ingredient_counts.get(x, 0), x)
            )[:limit]
            
            return sorted_ingredients
            
        except Exception as e:
            logger.error(f"Failed to get ingredients: {e}", exc_info=True)
            return []
        finally:
            session.close()
    
    def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict]:
        """
        Get recipe by ID
        
        Args:
            recipe_id: Recipe ID
            
        Returns:
            Recipe dictionary or None
        """
        session = self.get_session()
        try:
            recipe = session.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
            if not recipe:
                return None
            
            return {
                "recipe_id": recipe.recipe_id,
                "name": recipe.name,
                "description": recipe.description,
                "ingredients_list": recipe.ingredients_list,
                "steps": recipe.steps,
                "minutes": recipe.minutes,
                "n_steps": recipe.n_steps,
                "n_ingredients": recipe.n_ingredients,
                "nutrition": recipe.nutrition,
                "tags": recipe.tags,
                "calories": recipe.calories,
                "total_fat": recipe.total_fat,
                "sugar": recipe.sugar,
                "sodium": recipe.sodium,
                "protein": recipe.protein,
                "saturated_fat": recipe.saturated_fat,
                "carbohydrates": recipe.carbohydrates,
            }
        except Exception as e:
            logger.error(f"Failed to get recipe: {e}")
            return None
        finally:
            session.close()

