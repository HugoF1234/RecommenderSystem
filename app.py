"""
Application entry point for Render deployment
This file is used by gunicorn: gunicorn app:app
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

