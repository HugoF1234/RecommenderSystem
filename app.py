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

# Run server when executed directly
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Save Eat API...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("⚡ Press CTRL+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=8000)

