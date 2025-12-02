#!/usr/bin/env python3
"""
Script de test pour PostgreSQL (local ou Render)
Teste la connexion et le chargement des données
"""

import sys
import os
from pathlib import Path

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_msg(message, status="info"):
    """Print colored message"""
    if status == "success":
        print(f"{GREEN}✅ {message}{RESET}")
    elif status == "error":
        print(f"{RED}❌ {message}{RESET}")
    elif status == "warning":
        print(f"{YELLOW}⚠️  {message}{RESET}")
    else:
        print(f"{BLUE}🔍 {message}{RESET}")

def parse_database_url(url):
    """Parse DATABASE_URL"""
    from urllib.parse import urlparse
    try:
        db_url = urlparse(url)
        return {
            "host": db_url.hostname,
            "port": db_url.port or 5432,
            "database": db_url.path[1:] if db_url.path else "saveeat",
            "user": db_url.username,
            "password": db_url.password
        }
    except Exception as e:
        print_msg(f"Erreur parsing DATABASE_URL: {e}", "error")
        return None

def test_connection(db_params):
    """Test PostgreSQL connection"""
    print_msg("\n1. Test de connexion PostgreSQL...")
    
    try:
        from src.api.database import Database, Recipe, Review
        
        db = Database(
            database_type="postgresql",
            **db_params
        )
        
        print_msg(f"Connexion réussie à {db_params['host']}", "success")
        
        # Test query
        session = db.get_session()
        recipe_count = session.query(Recipe).count()
        review_count = session.query(Review).count()
        
        print_msg(f"Recettes: {recipe_count}", "info")
        print_msg(f"Reviews: {review_count}", "info")
        
        if recipe_count == 0:
            print_msg("Base de données vide!", "warning")
            print_msg("Chargez les données avec: python scripts/load_to_postgres.py", "info")
            session.close()
            return False
        
        print_msg(f"Base de données OK: {recipe_count} recettes, {review_count} reviews", "success")
        
        # Test sample recipe
        if recipe_count > 0:
            sample = session.query(Recipe).first()
            if sample:
                print_msg(f"Exemple: {sample.name} (ID: {sample.recipe_id})", "info")
        
        session.close()
        return True
        
    except Exception as e:
        print_msg(f"Erreur de connexion: {e}", "error")
        import traceback
        traceback.print_exc()
        return False

def test_data_loading(db_params):
    """Test data loading from CSV"""
    print_msg("\n2. Test du chargement des données...")
    
    # Check if CSV files exist
    raw_path = Path("data/raw")
    possible_recipes = [
        raw_path / "recipes_clean_full.csv",
        raw_path / "recipes.csv",
    ]
    possible_reviews = [
        raw_path / "reviews_clean_full.csv",
        raw_path / "reviews.csv",
    ]
    
    recipes_file = None
    reviews_file = None
    
    for path in possible_recipes:
        if path.exists():
            recipes_file = path
            break
    
    for path in possible_reviews:
        if path.exists():
            reviews_file = path
            break
    
    if not recipes_file:
        print_msg("Fichier recipes CSV non trouvé dans data/raw/", "error")
        print_msg("Téléchargez depuis Kaggle: 'RecSys project dataset Food.com'", "info")
        return False
    
    if not reviews_file:
        print_msg("Fichier reviews CSV non trouvé dans data/raw/", "error")
        return False
    
    print_msg(f"CSV trouvés: {recipes_file.name}, {reviews_file.name}", "success")
    
    # Test loading
    try:
        from scripts.load_to_postgres import load_to_postgres
        
        print_msg("Chargement des données (cela peut prendre plusieurs minutes)...", "info")
        load_to_postgres(
            host=db_params["host"],
            port=db_params["port"],
            database=db_params["database"],
            user=db_params["user"],
            password=db_params["password"]
        )
        
        print_msg("Données chargées avec succès!", "success")
        return True
        
    except Exception as e:
        print_msg(f"Erreur de chargement: {e}", "error")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🧪 TEST POSTGRESQL - SAVE EAT{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # Get DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print_msg("DATABASE_URL non défini!", "error")
        print_msg("\nDéfinissez DATABASE_URL:", "info")
        print("  export DATABASE_URL='postgresql://user:pass@host:5432/database'")
        print("\nPour Render PostgreSQL:")
        print("  1. Render Dashboard → PostgreSQL → Connections")
        print("  2. Copiez 'Internal Database URL' (pour web service)")
        print("  3. Ou 'External Connection String' (pour local)")
        return 1
    
    # Parse URL
    print_msg("DATABASE_URL trouvé", "success")
    db_params = parse_database_url(database_url)
    
    if not db_params:
        return 1
    
    print_msg(f"Host: {db_params['host']}", "info")
    print_msg(f"Database: {db_params['database']}", "info")
    print_msg(f"User: {db_params['user']}", "info")
    
    # Test connection
    connection_ok = test_connection(db_params)
    
    if not connection_ok:
        print_msg("\n⚠️  Connexion échouée ou base vide", "warning")
        
        # Ask if user wants to load data
        try:
            response = input(f"\n{YELLOW}Voulez-vous charger les données maintenant? (y/n): {RESET}")
            if response.lower() in ['y', 'yes', 'o', 'oui']:
                data_ok = test_data_loading(db_params)
                if data_ok:
                    # Test connection again
                    connection_ok = test_connection(db_params)
        except KeyboardInterrupt:
            print("\n")
            print_msg("Annulé par l'utilisateur", "info")
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}📊 RÉSUMÉ{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    if connection_ok:
        print_msg("PostgreSQL fonctionne correctement!", "success")
        print_msg("\n✅ Vous pouvez déployer sur Render avec PostgreSQL", "info")
        print_msg("   Ajoutez DATABASE_URL dans les variables d'environnement Render", "info")
        return 0
    else:
        print_msg("Des problèmes ont été détectés", "error")
        print_msg("\nVérifiez:", "info")
        print("  1. PostgreSQL est démarré (local) ou créé (Render)")
        print("  2. DATABASE_URL est correct")
        print("  3. Les credentials sont valides")
        print("  4. Les CSV sont dans data/raw/")
        return 1

if __name__ == "__main__":
    sys.exit(main())

