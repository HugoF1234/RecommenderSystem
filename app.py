"""
Application entry point for Save Eat
Can be used for:
- Direct execution: python app.py
- Render deployment: gunicorn app:app
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app
from src.api.main import app

# Export app for gunicorn
__all__ = ["app"]

# Auto-initialize database if needed
def ensure_database_ready():
    """Ensure database has data, load if necessary"""
    from src.api.database import Database, Recipe, Review
    from pathlib import Path
    import gzip
    import shutil
    
    db_path = Path("data/saveeat.db")
    db_gz_path = Path("data/saveeat.db.gz")
    
    # If compressed database exists but not uncompressed, extract it
    if db_gz_path.exists() and not db_path.exists():
        print("📦 Extracting database from archive...")
        with gzip.open(db_gz_path, 'rb') as f_in:
            with open(db_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print("✅ Database extracted successfully!")
    
    # Check if database exists and has data
    if db_path.exists():
        db = Database(database_type="sqlite", sqlite_path=str(db_path))
        session = db.get_session()
        recipe_count = session.query(Recipe).count()
        review_count = session.query(Review).count()
        session.close()
        
        if recipe_count > 0:
            print(f"✅ Database ready: {recipe_count} recipes, {review_count} reviews")
            return True
    
    # Database missing or empty - check if we can extract from compressed file
    # If compressed DB exists, it will be extracted by startup_event in src/api/main.py
    # If not, the preprocessing will handle loading data from CSV if available
    print("📦 Database is empty or missing")
    print("   The system will attempt to:")
    print("   1. Extract database from data/saveeat.db.gz (if available)")
    print("   2. Generate processed files automatically from database")
    print("   This will happen during API startup...")
    return True  # Allow startup to continue - preprocessing will handle data loading

# Run server when executed directly
if __name__ == "__main__":
    import uvicorn
    
    # Ensure database is ready
    if not ensure_database_ready():
        print("\n❌ Database initialization failed")
        print("   Please check that data files exist:")
        print("   - data/processed/recipes.csv")
        print("   - data/raw/reviews.csv (optional)")
        sys.exit(1)
    
    print("\n🚀 Starting Save Eat API...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("⚡ Press CTRL+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)

