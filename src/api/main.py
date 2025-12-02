"""
FastAPI Main Application for Save Eat
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn
import yaml
import logging

from .endpoints import router, initialize_model
from .database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database instance
db_instance = None

# Create FastAPI app
app = FastAPI(
    title="Save Eat API",
    description="Recipe Recommendation System API",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["recommendations"])

# Mount static files and serve frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if (frontend_path / "index.html").exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")
    
    @app.get("/")
    async def serve_frontend():
        """Serve frontend index page"""
        return FileResponse(str(frontend_path / "index.html"))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Initialize model and data on startup"""
    global db_instance
    
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            
            # Initialize database
            db_config = config.get("database", {})
            db_instance = Database(
                database_type=db_config.get("type", "sqlite"),
                sqlite_path=db_config.get("sqlite_path", "data/saveeat.db"),
                **db_config.get("postgresql", {})
            )
            logger.info("Database initialized")
            
            # Check if database has recipes, if not, try to auto-load from CSV
            session = db_instance.get_session()
            try:
                from .database import Recipe
                recipe_count = session.query(Recipe).count()
                if recipe_count == 0:
                    logger.info("No recipes in database. Attempting to auto-load from CSV...")
                    # Try to auto-load if CSV files exist
                    recipes_path = None
                    possible_paths = [
                        Path("data/raw/recipes_clean_full.csv"),
                        Path("data/raw/recipes.csv"),
                        Path("data/processed/recipes.csv"),
                    ]
                    
                    for path in possible_paths:
                        if path.exists():
                            recipes_path = path
                            break
                    
                    if recipes_path:
                        try:
                            logger.info(f"Found recipes CSV at {recipes_path}, loading...")
                            db_instance.load_recipes_from_csv(str(recipes_path))
                            recipe_count = session.query(Recipe).count()
                            logger.info(f"Successfully loaded {recipe_count} recipes into database")
                        except Exception as e:
                            logger.warning(f"Failed to auto-load recipes: {e}")
                            logger.info("Please run: python main.py load-db")
                    else:
                        logger.warning("No recipes CSV found. Please run: python main.py load-db")
                else:
                    logger.info(f"Database has {recipe_count} recipes")
            finally:
                session.close()
            
            # Initialize model (placeholder - implement based on actual model loading)
            model_path = Path("models/checkpoints/best_model.pt")
            graph_data_path = Path("data/processed/graph.pt")
            recipe_data_path = Path("data/processed/recipes.csv")
            mappings_path = Path("data/processed/mappings.pkl")
            
            # Check if files exist before initializing
            if model_path.exists():
                initialize_model(str(model_path), str(graph_data_path), str(recipe_data_path), str(mappings_path))
            else:
                logger.warning("Model not found - API will run but recommendations won't work")
        else:
            logger.warning("Config file not found")
            # Initialize database with defaults
            db_instance = Database(database_type="sqlite", sqlite_path="data/saveeat.db")
            
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        # Initialize database with defaults even on error
        try:
            db_instance = Database(database_type="sqlite", sqlite_path="data/saveeat.db")
        except:
            pass


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
