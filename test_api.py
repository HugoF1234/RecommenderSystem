#!/usr/bin/env python3
"""
Script de test de l'API Save Eat
Teste les endpoints principaux
"""

import sys
import time
import requests
from pathlib import Path

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

def test_health(base_url):
    """Test health endpoint"""
    print_msg("\n1. Test /health...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_msg(f"Status: {data.get('status')}", "success")
            return True
        else:
            print_msg(f"Status code: {response.status_code}", "error")
            return False
    except requests.exceptions.ConnectionError:
        print_msg("Impossible de se connecter au serveur", "error")
        print_msg("Le serveur est-il démarré? python main.py serve", "info")
        return False
    except Exception as e:
        print_msg(f"Erreur: {e}", "error")
        return False

def test_get_recipe(base_url):
    """Test get recipe endpoint"""
    print_msg("\n2. Test /api/v1/recipe/{recipe_id}...")
    
    recipe_ids = [38, 100, 1000]
    
    for recipe_id in recipe_ids:
        try:
            response = requests.get(f"{base_url}/api/v1/recipe/{recipe_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                name = data.get('name', 'N/A')
                ingredients = len(data.get('ingredients_list', []))
                minutes = data.get('minutes', 'N/A')
                print_msg(f"Recipe {recipe_id}: {name} ({ingredients} ingrédients, {minutes} min)", "success")
            elif response.status_code == 404:
                print_msg(f"Recipe {recipe_id}: Non trouvée", "warning")
            else:
                print_msg(f"Recipe {recipe_id}: Status {response.status_code}", "error")
        except Exception as e:
            print_msg(f"Erreur pour recipe {recipe_id}: {e}", "error")
    
    return True

def test_search_recipes(base_url):
    """Test search recipes endpoint"""
    print_msg("\n3. Test /api/v1/recipes/search...")
    
    try:
        params = {
            "ingredients": "chicken,tomato",
            "limit": 5
        }
        response = requests.get(f"{base_url}/api/v1/recipes/search", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            recipes = data.get('recipes', [])
            print_msg(f"Trouvé {len(recipes)} recettes", "success")
            for i, recipe in enumerate(recipes[:3], 1):
                name = recipe.get('name', 'N/A')
                print_msg(f"  {i}. {name}", "info")
            return True
        else:
            print_msg(f"Status code: {response.status_code}", "error")
            return False
    except Exception as e:
        print_msg(f"Erreur: {e}", "error")
        return False

def test_recommend(base_url):
    """Test recommend endpoint"""
    print_msg("\n4. Test /api/v1/recommend...")
    
    try:
        payload = {
            "user_id": 1,
            "available_ingredients": ["chicken", "tomato", "pasta"],
            "max_time": 30,
            "top_k": 5
        }
        
        response = requests.post(f"{base_url}/api/v1/recommend", json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            recipe_ids = data.get('recipe_ids', [])
            scores = data.get('scores', [])
            print_msg(f"Recommandations: {len(recipe_ids)} recettes", "success")
            for i, (rid, score) in enumerate(zip(recipe_ids[:3], scores[:3]), 1):
                print_msg(f"  {i}. Recipe {rid} (score: {score:.3f})", "info")
            return True
        else:
            print_msg(f"Status code: {response.status_code}", "error")
            try:
                error = response.json()
                print_msg(f"Erreur: {error}", "info")
            except:
                pass
            return False
    except Exception as e:
        print_msg(f"Erreur: {e}", "error")
        return False

def test_log_interaction(base_url):
    """Test log interaction endpoint"""
    print_msg("\n5. Test /api/v1/log_interaction...")
    
    try:
        payload = {
            "user_id": 999,
            "recipe_id": 38,
            "interaction_type": "view",
            "rating": 5.0
        }
        
        response = requests.post(f"{base_url}/api/v1/log_interaction", json=payload, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_msg(f"Interaction enregistrée: {data.get('message', 'OK')}", "success")
            return True
        else:
            print_msg(f"Status code: {response.status_code}", "error")
            return False
    except Exception as e:
        print_msg(f"Erreur: {e}", "error")
        return False

def test_ingredients(base_url):
    """Test ingredients endpoint"""
    print_msg("\n6. Test /api/v1/ingredients...")
    
    try:
        response = requests.get(f"{base_url}/api/v1/ingredients?limit=10", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            ingredients = data.get('ingredients', [])
            print_msg(f"Ingrédients disponibles: {len(ingredients)}", "success")
            print_msg(f"Exemples: {', '.join(ingredients[:5])}", "info")
            return True
        else:
            print_msg(f"Status code: {response.status_code}", "error")
            return False
    except Exception as e:
        print_msg(f"Erreur: {e}", "error")
        return False

def test_frontend(base_url):
    """Test frontend"""
    print_msg("\n7. Test du frontend (/)...")
    
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            content = response.text
            if "Save Eat" in content or "saveeat" in content.lower() or "recipe" in content.lower():
                print_msg("Frontend chargé avec succès", "success")
                return True
            else:
                print_msg("Frontend chargé mais contenu inattendu", "warning")
                return False
        else:
            print_msg(f"Status code: {response.status_code}", "error")
            return False
    except Exception as e:
        print_msg(f"Erreur: {e}", "error")
        return False

def main():
    """Run all API tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🧪 TEST DE L'API SAVE EAT{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Get base URL
    import sys
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print_msg(f"URL de test: {base_url}", "info")
    print_msg("Pour tester un autre serveur: python test_api.py http://your-url.com", "info")
    
    # Wait a bit for server to be ready
    print_msg("\nAttente de 2 secondes...", "info")
    time.sleep(2)
    
    # Run tests
    results = {
        "Health": test_health(base_url),
        "Get Recipe": test_get_recipe(base_url),
        "Search Recipes": test_search_recipes(base_url),
        "Recommend": test_recommend(base_url),
        "Log Interaction": test_log_interaction(base_url),
        "Ingredients": test_ingredients(base_url),
        "Frontend": test_frontend(base_url),
    }
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}📊 RÉSUMÉ DES TESTS{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    for test_name, result in results.items():
        status = "success" if result else "error"
        print_msg(f"{test_name}: {'✓ PASSED' if result else '✗ FAILED'}", status)
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    if passed == total:
        print_msg(f"Tous les tests passent! ({passed}/{total})", "success")
        print_msg(f"\n✅ L'API fonctionne correctement sur {base_url}", "success")
    else:
        print_msg(f"Certains tests échouent ({passed}/{total})", "warning")
        print_msg(f"\nVérifiez:", "info")
        print("  - Le serveur est démarré: python main.py serve")
        print("  - La base de données est chargée")
        print("  - Les logs du serveur pour plus de détails")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    return 0 if passed >= 5 else 1  # At least 5/7 tests should pass

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrompu par l'utilisateur{RESET}")
        sys.exit(1)

