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
            import os
            
            # IMPORTANT: Auto-extract database if needed (for fresh deployments)
            db_path = Path("data/saveeat.db")
            db_gz_path = Path("data/saveeat.db.gz")
            if db_gz_path.exists() and not db_path.exists():
                import gzip
                import shutil
                logger.info("📦 Extracting database from archive...")
                try:
                    with gzip.open(db_gz_path, 'rb') as f_in:
                        with open(db_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    logger.info("✅ Database extracted successfully!")
                except Exception as e:
                    logger.error(f"❌ Failed to extract database: {e}")
            
            # Priority: Use PostgreSQL if DATABASE_URL is set (regardless of config.yaml)
            if os.getenv("DATABASE_URL"):
                try:
                    from urllib.parse import urlparse
                    db_url = urlparse(os.getenv("DATABASE_URL"))
                    logger.info(f"Using PostgreSQL from DATABASE_URL: {db_url.hostname}")
                    db_instance = Database(
                        database_type="postgresql",
                        host=db_url.hostname,
                        port=db_url.port or 5432,
                        database=db_url.path[1:] if db_url.path else "saveeat",
                        user=db_url.username,
                        password=db_url.password
                    )
                except Exception as e:
                    logger.warning(f"Failed to connect to PostgreSQL: {e}, using SQLite instead")
                    db_instance = Database(
                        database_type="sqlite",
                        sqlite_path=db_config.get("sqlite_path", "data/saveeat.db")
                    )
            else:
                # Default: SQLite - works everywhere, no config needed!
                logger.info("Using SQLite database (default - no PostgreSQL needed)")
                db_instance = Database(
                    database_type="sqlite",
                    sqlite_path=db_config.get("sqlite_path", "data/saveeat.db")
                )
            logger.info("Database initialized")
            
            # Check if database has recipes
            session = db_instance.get_session()
            try:
                from .database import Recipe
                recipe_count = session.query(Recipe).count()
                if recipe_count == 0:
                    logger.warning(f"Database is empty ({recipe_count} recipes). Please load data using: python main.py load-db")
                    logger.info("The API will work but won't return any recommendations until data is loaded.")
                else:
                    logger.info(f"Database initialized with {recipe_count} recipes")
            except Exception as e:
                logger.error(f"Error checking database: {e}")
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
            logger.warning("Config file not found, using defaults")
            # Initialize database with smart defaults
            import os
            if os.getenv("DATABASE_URL"):
                try:
                    from urllib.parse import urlparse
                    db_url = urlparse(os.getenv("DATABASE_URL"))
                    db_instance = Database(
                        database_type="postgresql",
                        host=db_url.hostname,
                        port=db_url.port or 5432,
                        database=db_url.path[1:] if db_url.path else "saveeat",
                        user=db_url.username,
                        password=db_url.password
                    )
                except:
                    db_instance = Database(database_type="sqlite", sqlite_path="data/saveeat.db")
            else:
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
