#!/usr/bin/env python3
"""
Script de diagnostic pour déploiement Render
Vérifie que tous les fichiers sont prêts
"""

import sys
from pathlib import Path
import os

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_msg(message, status="info"):
    if status == "success":
        print(f"{GREEN}✅ {message}{RESET}")
    elif status == "error":
        print(f"{RED}❌ {message}{RESET}")
    elif status == "warning":
        print(f"{YELLOW}⚠️  {message}{RESET}")
    else:
        print(f"{BLUE}🔍 {message}{RESET}")

def check_files():
    """Check required files exist"""
    print_msg("\n1. Vérification des fichiers de déploiement...")
    
    required_files = {
        "build.sh": "Script de build Render",
        "start.sh": "Script de démarrage",
        "app.py": "Point d'entrée pour gunicorn/uvicorn",
        "requirements.txt": "Dépendances Python",
        "render.yaml": "Configuration Render (optionnel)",
        "runtime.txt": "Version Python",
    }
    
    all_ok = True
    for file, description in required_files.items():
        path = Path(file)
        if path.exists():
            size = path.stat().st_size
            print_msg(f"{file}: {size} bytes - {description}", "success")
        else:
            if file == "render.yaml":
                print_msg(f"{file}: Manquant (optionnel)", "warning")
            else:
                print_msg(f"{file}: Manquant - {description}", "error")
                all_ok = False
    
    return all_ok

def check_app_py():
    """Check app.py exports app correctly"""
    print_msg("\n2. Vérification de app.py...")
    
    try:
        # Import app
        from app import app
        print_msg("app importé avec succès", "success")
        
        # Check it's a FastAPI app
        from fastapi import FastAPI
        if isinstance(app, FastAPI):
            print_msg("app est une instance FastAPI", "success")
        else:
            print_msg(f"app n'est pas une instance FastAPI (type: {type(app)})", "error")
            return False
        
        # Check routes exist
        routes = [route.path for route in app.routes]
        if "/health" in routes:
            print_msg("Route /health trouvée", "success")
        else:
            print_msg("Route /health manquante", "warning")
        
        return True
        
    except Exception as e:
        print_msg(f"Erreur import app: {e}", "error")
        import traceback
        traceback.print_exc()
        return False

def check_build_script():
    """Check build.sh is valid"""
    print_msg("\n3. Vérification de build.sh...")
    
    path = Path("build.sh")
    if not path.exists():
        print_msg("build.sh manquant", "error")
        return False
    
    content = path.read_text()
    
    checks = {
        "pip install --upgrade pip": "Upgrade pip",
        "pip install torch": "Installation PyTorch",
        "pip install -r requirements.txt": "Installation dépendances",
        "--index-url https://download.pytorch.org/whl/cpu": "PyTorch CPU-only (économie d'espace)",
    }
    
    all_ok = True
    for check, description in checks.items():
        if check in content:
            print_msg(f"✓ {description}", "success")
        else:
            if "cpu" in check:
                print_msg(f"⚠ {description} (recommandé pour Render)", "warning")
            else:
                print_msg(f"✗ {description}", "error")
                all_ok = False
    
    # Check executable
    import stat
    mode = path.stat().st_mode
    is_executable = bool(mode & stat.S_IXUSR)
    if is_executable:
        print_msg("build.sh est exécutable", "success")
    else:
        print_msg("build.sh n'est pas exécutable", "warning")
        print_msg("  Corrigez avec: chmod +x build.sh", "info")
    
    return all_ok

def check_start_script():
    """Check start.sh is valid"""
    print_msg("\n4. Vérification de start.sh...")
    
    path = Path("start.sh")
    if not path.exists():
        print_msg("start.sh manquant", "error")
        return False
    
    content = path.read_text()
    
    if "uvicorn" in content and "app:app" in content:
        print_msg("Commande uvicorn trouvée", "success")
    elif "gunicorn" in content:
        print_msg("Commande gunicorn trouvée", "success")
    else:
        print_msg("Commande de démarrage non trouvée", "error")
        return False
    
    if "${PORT" in content or "$PORT" in content:
        print_msg("Variable PORT utilisée", "success")
    else:
        print_msg("Variable PORT manquante (Render utilise PORT)", "warning")
    
    if "--host 0.0.0.0" in content:
        print_msg("Host 0.0.0.0 configuré", "success")
    else:
        print_msg("Host 0.0.0.0 manquant", "warning")
    
    return True

def check_requirements():
    """Check requirements.txt"""
    print_msg("\n5. Vérification de requirements.txt...")
    
    path = Path("requirements.txt")
    if not path.exists():
        print_msg("requirements.txt manquant", "error")
        return False
    
    content = path.read_text()
    
    required_packages = {
        "torch": "PyTorch",
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn (serveur ASGI)",
        "sqlalchemy": "SQLAlchemy (ORM)",
        "psycopg2": "PostgreSQL driver",
    }
    
    all_ok = True
    for package, description in required_packages.items():
        if package in content.lower():
            print_msg(f"✓ {description}", "success")
        else:
            print_msg(f"✗ {description} manquant", "error")
            all_ok = False
    
    return all_ok

def check_database_files():
    """Check database files"""
    print_msg("\n6. Vérification de la base de données...")
    
    sqlite_path = Path("data/saveeat.db")
    
    if sqlite_path.exists():
        size_mb = sqlite_path.stat().st_size / (1024 * 1024)
        print_msg(f"SQLite database: {size_mb:.1f} MB", "success")
        
        # Test database
        try:
            from src.api.database import Database, Recipe
            db = Database(database_type="sqlite", sqlite_path=str(sqlite_path))
            session = db.get_session()
            count = session.query(Recipe).count()
            session.close()
            print_msg(f"Database contient {count} recettes", "success")
        except Exception as e:
            print_msg(f"Erreur lecture database: {e}", "warning")
    else:
        print_msg("SQLite database manquante (data/saveeat.db)", "warning")
        print_msg("  Options:", "info")
        print("    1. Chargez les données: python main.py load-db")
        print("    2. Ou utilisez PostgreSQL sur Render")
    
    return True

def check_gitignore():
    """Check .gitignore"""
    print_msg("\n7. Vérification de .gitignore...")
    
    path = Path(".gitignore")
    if not path.exists():
        print_msg(".gitignore manquant", "warning")
        return True
    
    content = path.read_text()
    
    # Check if database is ignored (bad for deployment)
    if "saveeat.db" in content or "*.db" in content:
        print_msg("⚠️  Base de données SQLite ignorée par git", "warning")
        print_msg("  Pour Render avec SQLite:", "info")
        print("    1. Option A: Retirez *.db de .gitignore et commitez la DB")
        print("    2. Option B: Uploadez manuellement via Render Shell")
        print("    3. Option C: Utilisez PostgreSQL à la place")
    else:
        print_msg("Base de données non ignorée (bon pour déploiement)", "success")
    
    return True

def check_environment():
    """Check environment variables"""
    print_msg("\n8. Variables d'environnement (pour Render)...")
    
    print_msg("Variables nécessaires sur Render:", "info")
    
    # Check if DATABASE_URL is set locally (for testing)
    if os.getenv("DATABASE_URL"):
        print_msg("DATABASE_URL défini localement", "success")
    else:
        print_msg("DATABASE_URL non défini (normal en local)", "info")
    
    print("\n  Pour SQLite sur Render:")
    print("    ✅ Aucune variable nécessaire !")
    print("    ✅ Uploadez data/saveeat.db")
    
    print("\n  Pour PostgreSQL sur Render:")
    print("    📝 DATABASE_URL = <Internal Database URL>")
    print("       (Copiez depuis Render PostgreSQL → Connections)")
    
    return True

def print_summary(results):
    """Print summary"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}📊 RÉSUMÉ DU DIAGNOSTIC{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    for check, result in results.items():
        status = "success" if result else "error"
        print_msg(f"{check}: {'✓' if result else '✗'}", status)
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    if passed == total:
        print_msg(f"Tous les checks passent! ({passed}/{total})", "success")
        print_msg("\n🚀 Votre projet est prêt pour Render!", "success")
        print("\nProchaines étapes:")
        print("  1. Commitez et pushez sur GitHub")
        print("  2. Créez un Web Service sur Render")
        print("  3. Configurez les variables d'environnement si besoin")
        print("  4. Uploadez data/saveeat.db (si vous utilisez SQLite)")
        print("\nDocumentation: RENDER_DEPLOYMENT_GUIDE.md")
    else:
        print_msg(f"Des problèmes détectés ({passed}/{total})", "error")
        print_msg("\nCorrigez les erreurs avant de déployer", "warning")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    return passed == total

def main():
    """Run all checks"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🔍 DIAGNOSTIC DE DÉPLOIEMENT RENDER{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    results = {
        "Fichiers requis": check_files(),
        "app.py": check_app_py(),
        "build.sh": check_build_script(),
        "start.sh": check_start_script(),
        "requirements.txt": check_requirements(),
        "Base de données": check_database_files(),
        ".gitignore": check_gitignore(),
        "Variables d'environnement": check_environment(),
    }
    
    success = print_summary(results)
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrompu par l'utilisateur{RESET}")
        sys.exit(1)

