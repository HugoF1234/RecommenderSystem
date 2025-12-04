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
import threading

from .endpoints import router, initialize_model
from .database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database instance and cache
db_instance = None
_ingredients_cache = None


def _precalculate_ingredients_cache():
    """
    Pre-calculate ingredients cache in background thread (after port binding)
    This prevents Render timeout during startup
    """
    global _ingredients_cache
    try:
        logger.info("🔄 Pre-calculating ingredients cache in background...")
        _ingredients_cache = db_instance.get_all_ingredients(500)
        logger.info(f"✅ Cached {len(_ingredients_cache)} ingredients")
    except Exception as e:
        logger.error(f"Failed to pre-calculate ingredients cache: {e}")
        _ingredients_cache = []

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
                    
                    # Schedule ingredients cache pre-calculation in background thread (after port binding!)
                    # This prevents Render timeout during startup - server binds port first, then cache loads
                    cache_thread = threading.Thread(target=_precalculate_ingredients_cache, daemon=True)
                    cache_thread.start()
                    logger.info("🚀 Started background cache pre-calculation (server will bind port immediately)")
                    
            except Exception as e:
                logger.error(f"Error checking database: {e}")
            finally:
                session.close()
            
            # Initialize model (can work with or without trained checkpoint)
            model_path = Path("models/checkpoints/best_model.pt")
            graph_data_path = Path("data/processed/graph.pt")
            recipe_data_path = Path("data/processed/recipes.csv")
            mappings_path = Path("data/processed/mappings.pkl")
            
            # Check if essential files exist (mappings, graph, recipes are required)
            # Model checkpoint is optional (will use random weights if not found)
            essential_files_exist = (
                mappings_path.exists() and 
                graph_data_path.exists() and 
                recipe_data_path.exists()
            )
            
            if not essential_files_exist:
                # Auto-generate processed files from database (for seamless 5-step setup)
                logger.info("📦 Essential processed files not found. Auto-generating from database...")
                logger.info("   This will take 2-3 minutes on first run...")
                
                try:
                    # Check if database has data
                    session = db_instance.get_session()
                    from .database import Recipe, Review
                    recipe_count = session.query(Recipe).count()
                    review_count = session.query(Review).count()
                    session.close()
                    
                    if recipe_count > 0:
                        logger.info(f"   Found {recipe_count} recipes and {review_count} reviews in database")
                        logger.info("   Running preprocessing pipeline...")
                        
                        # Import preprocessing function
                        from src.data.db_to_processed import preprocess_from_db
                        import os
                        
                        # Determine database type and path
                        db_type = "sqlite"
                        db_path_str = "data/saveeat.db"
                        if os.getenv("DATABASE_URL"):
                            db_type = "postgresql"
                            db_path_str = os.getenv("DATABASE_URL")
                        
                        # Run preprocessing
                        processed_data, graph_data = preprocess_from_db(
                            db_path=db_path_str,
                            database_type=db_type,
                            output_path=Path("data/processed")
                        )
                        
                        logger.info("✅ Preprocessing complete!")
                        logger.info(f"   - {processed_data['stats']['n_users']} users")
                        logger.info(f"   - {processed_data['stats']['n_recipes']} recipes")
                        logger.info(f"   - Graph: {graph_data.num_nodes} nodes, {graph_data.num_edges} edges")
                        
                        # Files should now exist, continue to model initialization
                        essential_files_exist = True
                    else:
                        logger.warning("⚠️  Database is empty. Cannot generate processed files.")
                        logger.warning("   Please ensure database has data (recipes and reviews)")
                        logger.warning("   API will run but recommendations will use fallback method")
                except Exception as e:
                    logger.error(f"❌ Failed to auto-generate processed files: {e}")
                    logger.error("   API will run but recommendations will use fallback method")
                    import traceback
                    logger.debug(traceback.format_exc())
            
            if essential_files_exist:
                # Initialize model (will use checkpoint if available, otherwise random weights)
                initialize_model(
                    str(model_path) if model_path.exists() else None,
                    str(graph_data_path), 
                    str(recipe_data_path), 
                    str(mappings_path)
                )
            else:
                missing_files = []
                if not mappings_path.exists():
                    missing_files.append(f"mappings.pkl ({mappings_path})")
                if not graph_data_path.exists():
                    missing_files.append(f"graph.pt ({graph_data_path})")
                if not recipe_data_path.exists():
                    missing_files.append(f"recipes.csv ({recipe_data_path})")
                
                logger.warning("⚠️  Model cannot be loaded - missing essential files:")
                for file in missing_files:
                    logger.warning(f"   - {file}")
                logger.warning("   API will run but recommendations will use fallback method")
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
