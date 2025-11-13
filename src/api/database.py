"""
Database module for Save Eat
Manages PostgreSQL/SQLite database for interactions
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from typing import Optional, Dict, List
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


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

