"""
Database module for Save Eat
Manages PostgreSQL/SQLite database for interactions
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, JSON, func, desc, nullslast
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
    steps_list = Column(JSON, nullable=True)  # List of steps as JSON
    image_url = Column(String, nullable=True)  # Recipe image URL
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


class UserProfile(Base):
    """
    User profile table for storing user preferences and information
    """
    __tablename__ = "user_profiles"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True, unique=True)

    # Dietary preferences
    dietary_restrictions = Column(JSON, nullable=True)  # ["vegetarian", "vegan", "gluten-free", etc.]
    allergies = Column(JSON, nullable=True)  # ["nuts", "dairy", "eggs", etc.]

    # Cuisine preferences
    favorite_cuisines = Column(JSON, nullable=True)  # ["italian", "mexican", "asian", etc.]
    disliked_ingredients = Column(JSON, nullable=True)  # List of ingredients to avoid
    favorite_ingredients = Column(JSON, nullable=True)  # List of preferred ingredients

    # Nutritional preferences
    max_calories = Column(Float, nullable=True)  # Maximum calories per recipe
    min_protein = Column(Float, nullable=True)  # Minimum protein (g)
    max_carbs = Column(Float, nullable=True)  # Maximum carbs (g)
    max_fat = Column(Float, nullable=True)  # Maximum fat (g)

    # Cooking preferences
    max_prep_time = Column(Float, nullable=True)  # Maximum preparation time in minutes
    skill_level = Column(String, nullable=True)  # "beginner", "intermediate", "advanced"

    # Taste preferences (scale 0-10)
    spice_tolerance = Column(Integer, nullable=True)  # 0 (no spice) to 10 (very spicy)
    sweetness_preference = Column(Integer, nullable=True)  # 0 (not sweet) to 10 (very sweet)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
                        
                        # Parse steps_list
                        steps_list = None
                        steps_text = None
                        if "steps_list" in row and pd.notna(row["steps_list"]):
                            try:
                                steps_list = ast.literal_eval(str(row["steps_list"]))
                            except:
                                steps_list = None
                        if "steps_text" in row and pd.notna(row["steps_text"]):
                            steps_text = str(row["steps_text"])
                        elif "steps" in row and pd.notna(row["steps"]):
                            steps_text = str(row["steps"])
                        
                        # Get image_url
                        image_url = None
                        if "image_url" in row and pd.notna(row["image_url"]):
                            image_url = str(row["image_url"])
                        elif "Images" in row and pd.notna(row["Images"]):
                            try:
                                # Try to extract first URL from R-style format
                                images_str = str(row["Images"])
                                if 'http' in images_str:
                                    import re
                                    urls = re.findall(r'https?://[^\s,"]+', images_str)
                                    if urls:
                                        image_url = urls[0]
                            except:
                                pass
                        
                        recipe = Recipe(
                            recipe_id=int(row["recipe_id"]) if pd.notna(row.get("recipe_id")) else None,
                            name=str(row.get("name", "")) if pd.notna(row.get("name")) else str(row.get("Name", "")) if pd.notna(row.get("Name")) else "",
                            description=str(row.get("description", "")) if pd.notna(row.get("description")) else str(row.get("Description", "")) if pd.notna(row.get("Description")) else None,
                            ingredients_list=ingredients_list,
                            steps=steps_text,
                            steps_list=steps_list,
                            image_url=image_url,
                            minutes=float(row["minutes"]) if pd.notna(row.get("minutes")) else float(row["prep_time"]) if pd.notna(row.get("prep_time")) else None,
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
            # Check if reviews already exist with actual content
            existing_count = session.query(Review).count()
            existing_with_content = session.query(Review).filter(
                (Review.rating.isnot(None)) | (Review.review.isnot(None))
            ).count()
            
            # Only skip if reviews exist AND have content (rating or text)
            if existing_count > 0 and existing_with_content > 0:
                logger.info(f"Reviews table already has {existing_count} reviews with content. Skipping load.")
                return existing_count
            
            # If reviews exist but have no content, clear them and reload
            if existing_count > 0 and existing_with_content == 0:
                logger.warning(f"Found {existing_count} reviews but all have rating=None and review=None")
                logger.info("Clearing existing reviews to reload from CSV with correct mapping...")
                session.query(Review).delete()
                session.commit()
                logger.info("Cleared existing reviews")
            
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
            
            # Map review_clean to review (the CSV uses review_clean as column name)
            if "review_clean" in df.columns and "review" not in df.columns:
                df = df.rename(columns={"review_clean": "review"})
            
            # Map Rating to rating (case-insensitive)
            if "Rating" in df.columns and "rating" not in df.columns:
                df = df.rename(columns={"Rating": "rating"})
            
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
                        
                        # Get rating (already standardized to lowercase in df)
                        rating_val = None
                        if "rating" in row and pd.notna(row.get("rating")):
                            try:
                                rating_val = float(row["rating"])
                            except:
                                pass
                        
                        # Get review text (already standardized from review_clean to review in df)
                        review_text = None
                        if "review" in row and pd.notna(row.get("review")):
                            review_text = str(row["review"]).strip()
                            # Only use if not empty after stripping
                            if not review_text or review_text == "":
                                review_text = None
                        
                        review = Review(
                            user_id=int(row["user_id"]) if pd.notna(row.get("user_id")) else None,
                            recipe_id=int(row["recipe_id"]) if pd.notna(row.get("recipe_id")) else None,
                            rating=rating_val,
                            review=review_text if review_text else None,
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
    
    def get_popular_recipes_with_reviews(self, limit: int = 50, min_reviews: int = 3) -> List[Dict]:
        """
        Get popular recipes with highest average ratings and their reviews
        Note: If reviews don't have rating/text, we still return recipes with review count
        """
        """
        Get popular recipes with highest average ratings and their reviews
        Only returns recipes that have at least one review with rating or text
        
        Args:
            limit: Maximum number of recipes to return
            min_reviews: Minimum number of reviews required
            
        Returns:
            List of recipe dictionaries with reviews included
        """
        session = self.get_session()
        try:
            # Get recipes with review count
            # Since reviews don't have ratings in current DB, we order by review count
            recipes_with_stats = session.query(
                Recipe.recipe_id,
                Recipe.name,
                Recipe.description,
                Recipe.ingredients_list,
                Recipe.steps_list,
                Recipe.image_url,
                Recipe.minutes,
                Recipe.n_steps,
                Recipe.n_ingredients,
                Recipe.calories,
                Recipe.protein,
                Recipe.carbohydrates,
                Recipe.total_fat,
                func.count(Review.id).label('review_count')
            ).join(
                Review, Recipe.recipe_id == Review.recipe_id
            ).group_by(
                Recipe.recipe_id
            ).having(
                func.count(Review.id) >= min_reviews
            ).order_by(
                func.count(Review.id).desc()  # Order by review count (most reviewed first)
            ).limit(limit).all()
            
            result = []
            for recipe in recipes_with_stats:
                # Get 3-4 reviews for this recipe
                reviews = session.query(Review).filter(
                    Review.recipe_id == recipe.recipe_id
                ).order_by(
                    desc(Review.id)  # Order by ID desc (most recent first)
                ).limit(4).all()
                
                # Sort reviews in Python: date desc (nulls last), then id desc
                reviews = sorted(reviews, key=lambda r: (
                    r.date if r.date else datetime.min,
                    r.id
                ), reverse=True)[:4]
                
                # Build reviews list with proper handling of None values
                reviews_list = []
                for r in reviews:
                    review_dict = {
                        "user_id": r.user_id,
                        "rating": float(r.rating) if r.rating is not None else None,
                        "review": str(r.review).strip() if r.review and str(r.review).strip() else None,
                        "date": r.date.isoformat() if r.date else None
                    }
                    reviews_list.append(review_dict)
                
                logger.debug(f"Recipe {recipe.recipe_id}: {len(reviews_list)} reviews loaded")
                if len(reviews_list) > 0:
                    logger.debug(f"  First review: rating={reviews_list[0].get('rating')}, has_text={bool(reviews_list[0].get('review'))}, user_id={reviews_list[0].get('user_id')}")
                
                recipe_dict = {
                    "recipe_id": recipe.recipe_id,
                    "name": recipe.name,
                    "description": recipe.description,
                    "ingredients_list": recipe.ingredients_list,
                    "steps_list": recipe.steps_list,
                    "image_url": recipe.image_url,
                    "minutes": recipe.minutes,
                    "n_steps": recipe.n_steps,
                    "n_ingredients": recipe.n_ingredients,
                    "calories": float(recipe.calories) if recipe.calories else None,
                    "protein": float(recipe.protein) if recipe.protein else None,
                    "carbohydrates": float(recipe.carbohydrates) if recipe.carbohydrates else None,
                    "total_fat": float(recipe.total_fat) if recipe.total_fat else None,
                    "avg_rating": None,  # Reviews don't have ratings in current DB
                    "review_count": int(recipe.review_count) if recipe.review_count else 0,
                    "reviews": reviews_list
                }
                result.append(recipe_dict)
                
                # Stop when we have enough recipes
                if len(result) >= limit:
                    break
            
            logger.info(f"Retrieved {len(result)} popular recipes with contentful reviews")
            # Log sample of reviews for debugging
            if len(result) > 0 and len(result[0].get("reviews", [])) > 0:
                sample_review = result[0]["reviews"][0]
                logger.info(f"Sample review data: rating={sample_review.get('rating')}, has_text={bool(sample_review.get('review'))}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get popular recipes: {e}")
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
                "steps_list": recipe.steps_list,
                "image_url": recipe.image_url,
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

    def create_user_profile(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        **preferences
    ) -> Dict:
        """
        Create or update user profile

        Args:
            user_id: User ID
            username: Username
            email: Email address
            **preferences: Additional preference fields

        Returns:
            Created/updated profile dictionary
        """
        session = self.get_session()
        try:
            # Check if profile exists
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            if profile:
                # Update existing profile
                if username is not None:
                    profile.username = username
                if email is not None:
                    profile.email = email

                # Update preferences
                for key, value in preferences.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)

                profile.updated_at = datetime.utcnow()
                logger.info(f"Updated profile for user {user_id}")
            else:
                # Create new profile
                profile = UserProfile(
                    user_id=user_id,
                    username=username,
                    email=email,
                    **preferences
                )
                session.add(profile)
                logger.info(f"Created profile for user {user_id}")

            session.commit()
            session.refresh(profile)

            return self._profile_to_dict(profile)

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create/update profile: {e}")
            raise
        finally:
            session.close()

    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """
        Get user profile by user ID

        Args:
            user_id: User ID

        Returns:
            Profile dictionary or None
        """
        session = self.get_session()
        try:
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            if not profile:
                return None

            return self._profile_to_dict(profile)

        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            return None
        finally:
            session.close()

    def update_user_preferences(
        self,
        user_id: int,
        preferences: Dict
    ) -> Dict:
        """
        Update specific user preferences

        Args:
            user_id: User ID
            preferences: Dictionary of preferences to update

        Returns:
            Updated profile dictionary
        """
        session = self.get_session()
        try:
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            if not profile:
                # Create new profile if doesn't exist
                profile = UserProfile(user_id=user_id)
                session.add(profile)

            # Update preferences
            for key, value in preferences.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)

            profile.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(profile)

            logger.info(f"Updated preferences for user {user_id}")
            return self._profile_to_dict(profile)

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update preferences: {e}")
            raise
        finally:
            session.close()

    def delete_user_profile(self, user_id: int) -> bool:
        """
        Delete user profile

        Args:
            user_id: User ID

        Returns:
            True if deleted, False otherwise
        """
        session = self.get_session()
        try:
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            if not profile:
                return False

            session.delete(profile)
            session.commit()
            logger.info(f"Deleted profile for user {user_id}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete profile: {e}")
            return False
        finally:
            session.close()

    def _profile_to_dict(self, profile: UserProfile) -> Dict:
        """
        Convert UserProfile object to dictionary

        Args:
            profile: UserProfile object

        Returns:
            Profile dictionary
        """
        return {
            "user_id": profile.user_id,
            "username": profile.username,
            "email": profile.email,
            "dietary_restrictions": profile.dietary_restrictions,
            "allergies": profile.allergies,
            "favorite_cuisines": profile.favorite_cuisines,
            "disliked_ingredients": profile.disliked_ingredients,
            "favorite_ingredients": profile.favorite_ingredients,
            "max_calories": profile.max_calories,
            "min_protein": profile.min_protein,
            "max_carbs": profile.max_carbs,
            "max_fat": profile.max_fat,
            "max_prep_time": profile.max_prep_time,
            "skill_level": profile.skill_level,
            "spice_tolerance": profile.spice_tolerance,
            "sweetness_preference": profile.sweetness_preference,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        }

