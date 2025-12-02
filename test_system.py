#!/usr/bin/env python3
"""
Script de test complet pour Save Eat
Vérifie que tout fonctionne correctement
"""

import sys
from pathlib import Path
import json

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(message, status="info"):
    """Print test message with color"""
    if status == "success":
        print(f"{GREEN}✅ {message}{RESET}")
    elif status == "error":
        print(f"{RED}❌ {message}{RESET}")
    elif status == "warning":
        print(f"{YELLOW}⚠️  {message}{RESET}")
    else:
        print(f"{BLUE}🔍 {message}{RESET}")

def test_imports():
    """Test if all imports work"""
    print_test("Test des imports...")
    
    try:
        import torch
        print_test(f"PyTorch {torch.__version__} OK", "success")
    except ImportError as e:
        print_test(f"PyTorch import failed: {e}", "error")
        return False
    
    try:
        import fastapi
        print_test(f"FastAPI OK", "success")
    except ImportError as e:
        print_test(f"FastAPI import failed: {e}", "error")
        return False
    
    try:
        import pandas
        print_test(f"Pandas OK", "success")
    except ImportError as e:
        print_test(f"Pandas import failed: {e}", "error")
        return False
    
    try:
        from src.api.database import Database, Recipe, Review
        print_test("Database modules OK", "success")
    except ImportError as e:
        print_test(f"Database import failed: {e}", "error")
        return False
    
    return True

def test_database():
    """Test database connection and data"""
    print_test("\nTest de la base de données...")
    
    try:
        from src.api.database import Database, Recipe, Review
        
        # Test SQLite
        db = Database(database_type="sqlite", sqlite_path="data/saveeat.db")
        session = db.get_session()
        
        recipe_count = session.query(Recipe).count()
        review_count = session.query(Review).count()
        
        print_test(f"SQLite: {recipe_count} recettes, {review_count} reviews", "success")
        
        if recipe_count == 0:
            print_test("Base de données vide! Chargez les données avec: python main.py load-db", "warning")
            session.close()
            return False
        
        # Test récupération d'une recette
        sample_recipe = session.query(Recipe).first()
        if sample_recipe:
            print_test(f"Exemple: {sample_recipe.name} (ID: {sample_recipe.recipe_id})", "success")
            if sample_recipe.ingredients_list:
                print_test(f"  Ingrédients: {len(sample_recipe.ingredients_list)} items", "info")
            if sample_recipe.minutes:
                print_test(f"  Temps de préparation: {sample_recipe.minutes} min", "info")
        
        # Test récupération des ingrédients
        ingredients = db.get_all_ingredients(limit=10)
        if ingredients:
            print_test(f"Ingrédients disponibles: {len(ingredients)} (ex: {ingredients[:3]})", "success")
        
        session.close()
        return True
        
    except Exception as e:
        print_test(f"Erreur database: {e}", "error")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration file"""
    print_test("\nTest du fichier de configuration...")
    
    try:
        import yaml
        config_path = Path("config/config.yaml")
        
        if not config_path.exists():
            print_test("config/config.yaml non trouvé", "error")
            return False
        
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        print_test(f"Dataset: {config['dataset']['name']}", "success")
        print_test(f"Database type: {config['database']['type']}", "success")
        print_test(f"API port: {config['api']['port']}", "success")
        
        return True
        
    except Exception as e:
        print_test(f"Erreur config: {e}", "error")
        return False

def test_data_files():
    """Test if data files exist"""
    print_test("\nTest des fichiers de données...")
    
    files_to_check = [
        ("data/saveeat.db", "Base de données SQLite", True),
        ("data/processed/recipes.csv", "Recettes préprocessées", False),
        ("data/processed/train.csv", "Données d'entraînement", False),
        ("data/processed/mappings.pkl", "Mappings", False),
        ("config/config.yaml", "Configuration", True),
    ]
    
    all_ok = True
    for file_path, description, required in files_to_check:
        path = Path(file_path)
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print_test(f"{description}: {size_mb:.1f} MB", "success")
        else:
            if required:
                print_test(f"{description} manquant", "error")
                all_ok = False
            else:
                print_test(f"{description} manquant (optionnel)", "warning")
    
    return all_ok

def test_api_startup():
    """Test if API can start"""
    print_test("\nTest du démarrage de l'API...")
    
    try:
        from src.api.main import app
        print_test("App FastAPI chargée", "success")
        
        # Check routes
        routes = [route.path for route in app.routes]
        important_routes = ["/health", "/api/v1/recommend", "/api/v1/recipe/{recipe_id}"]
        
        for route in important_routes:
            # Check if route exists (with or without parameters)
            route_base = route.split("{")[0] if "{" in route else route
            if any(r.startswith(route_base) for r in routes):
                print_test(f"Route {route} OK", "success")
            else:
                print_test(f"Route {route} manquante", "warning")
        
        return True
        
    except Exception as e:
        print_test(f"Erreur API: {e}", "error")
        import traceback
        traceback.print_exc()
        return False

def test_frontend():
    """Test if frontend files exist"""
    print_test("\nTest du frontend...")
    
    frontend_files = [
        "frontend/index.html",
        "frontend/static/app.js",
    ]
    
    all_ok = True
    for file_path in frontend_files:
        path = Path(file_path)
        if path.exists():
            print_test(f"{file_path} OK", "success")
        else:
            print_test(f"{file_path} manquant", "error")
            all_ok = False
    
    return all_ok

def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print(f"{BLUE}📊 RÉSUMÉ DES TESTS{RESET}")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    for test_name, result in results.items():
        status = "success" if result else "error"
        print_test(f"{test_name}: {'PASSED' if result else 'FAILED'}", status)
    
    print("\n" + "="*60)
    if passed == total:
        print_test(f"Tous les tests ont réussi! ({passed}/{total})", "success")
        print_test("\n🚀 Vous pouvez lancer le serveur avec: python main.py serve", "info")
    else:
        print_test(f"Certains tests ont échoué ({passed}/{total})", "error")
        print_test("\n⚠️  Corrigez les erreurs avant de lancer le serveur", "warning")
    print("="*60)
    
    return passed == total

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🧪 TEST COMPLET DU SYSTÈME SAVE EAT{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    results = {
        "Imports": test_imports(),
        "Configuration": test_config(),
        "Fichiers de données": test_data_files(),
        "Base de données": test_database(),
        "API FastAPI": test_api_startup(),
        "Frontend": test_frontend(),
    }
    
    success = print_summary(results)
    
    # Additional recommendations
    if success:
        print(f"\n{GREEN}✨ RECOMMANDATIONS{RESET}")
        print("1. Pour tester en local: python main.py serve")
        print("2. Accédez à: http://localhost:8000")
        print("3. API docs: http://localhost:8000/docs")
        print("4. Pour Render: Suivez RENDER_DEPLOYMENT_GUIDE.md")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

