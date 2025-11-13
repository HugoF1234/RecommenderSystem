"""
API module for Save Eat
FastAPI backend for recipe recommendations
"""

from .main import app
from .database import Database

__all__ = ["app", "Database"]

