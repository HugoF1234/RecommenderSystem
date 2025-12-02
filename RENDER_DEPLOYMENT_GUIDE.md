# 🚀 Guide Complet de Déploiement sur Render

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Option 1: Déploiement avec SQLite (Recommandé)](#option-1-déploiement-avec-sqlite-recommandé)
- [Option 2: Déploiement avec PostgreSQL](#option-2-déploiement-avec-postgresql)
- [Vérification et Tests](#vérification-et-tests)
- [Dépannage](#dépannage)

## Vue d'ensemble

Save Eat peut être déployé sur Render de deux façons:
1. **SQLite** (Simple, rapide, recommandé pour démo)
2. **PostgreSQL** (Production, plus complexe)

## Option 1: Déploiement avec SQLite (Recommandé)

### ✅ Avantages
- ✅ Aucune configuration de base de données externe
- ✅ Déploiement en 5 minutes
- ✅ Parfait pour la démo et le projet académique
- ✅ 522,517 recettes et 1,401,982 reviews déjà disponibles

### 📝 Étapes

#### 1. Créer le Web Service sur Render

1. Allez sur [Render Dashboard](https://dashboard.render.com/)
2. Cliquez sur **"New"** → **"Web Service"**
3. Connectez votre repository GitHub
4. Configuration:
   - **Name**: `saveeat-api` (ou votre choix)
   - **Region**: `Oregon` (ou la plus proche)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `chmod +x start.sh && ./start.sh`
   - **Instance Type**: `Free` ou `Starter`

5. **Variables d'environnement** (optionnelles pour SQLite):
   - Aucune variable requise ! SQLite fonctionne sans configuration.

6. Cliquez sur **"Create Web Service"**

#### 2. Uploader la Base de Données SQLite

La base de données `data/saveeat.db` (145 MB) contient déjà toutes les données.

**Option A: Via Git (Recommandé si < 100MB après compression)**

```bash
# Compresser la base de données
gzip -c data/saveeat.db > data/saveeat.db.gz

# Ajouter au git (si pas dans .gitignore)
git add data/saveeat.db.gz
git commit -m "Add compressed database"
git push origin main

# Puis dans build.sh, ajouter:
# gunzip -f data/saveeat.db.gz
```

**Option B: Via Render Shell**

1. Render Dashboard → Votre Web Service → **"Shell"**
2. Dans le shell Render:

```bash
# Créer le dossier data
mkdir -p data

# Créer un fichier temporaire pour uploader
# (Utilisez l'interface Render pour uploader le fichier)
```

**Option C: Via Render Disk (Persistant)**

1. Render Dashboard → **"Disks"** → **"New Disk"**
2. Configuration:
   - Name: `saveeat-data`
   - Size: `1 GB`
   - Mount Path: `/opt/render/project/src/data`
3. Attachez le disk à votre web service
4. Uploadez `saveeat.db` via Render Shell

#### 3. Vérifier le Déploiement

1. Attendez la fin du build (3-5 minutes)
2. Accédez à l'URL fournie par Render (ex: `https://saveeat-api.onrender.com`)
3. Testez les endpoints:
   - `https://saveeat-api.onrender.com/health` → `{"status":"healthy"}`
   - `https://saveeat-api.onrender.com/docs` → Documentation API

**C'est tout ! Votre application fonctionne avec SQLite !**

---

## Option 2: Déploiement avec PostgreSQL

### ✅ Avantages
- ✅ Meilleur pour la production à long terme
- ✅ Données persistantes et sauvegardées
- ✅ Meilleures performances pour les écritures intensives

### 📝 Étapes

#### 1. Créer PostgreSQL sur Render

1. Render Dashboard → **"New"** → **"PostgreSQL"**
2. Configuration:
   - **Name**: `saveeat-db`
   - **Database**: `saveeat`
   - **User**: (généré automatiquement)
   - **Region**: `Oregon` (même région que le web service)
   - **PostgreSQL Version**: `16`
   - **Plan**: `Free` (limité à 90 jours) ou `Starter`

3. Cliquez sur **"Create Database"**
4. Attendez la création (1-2 minutes)

#### 2. Configurer le Web Service

1. Créez le web service comme dans l'Option 1
2. **Variables d'environnement**:
   - **Clé**: `DATABASE_URL`
   - **Valeur**: Copiez l'**Internal Database URL** depuis votre PostgreSQL Render
     - Format: `postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/saveeat`
     - ⚠️ **Utilisez l'Internal URL, PAS l'External URL** (pour la communication entre services Render)

#### 3. Charger les Données dans PostgreSQL

**Option A: Depuis votre machine locale (Recommandé)**

```bash
# 1. Copiez l'External Database URL depuis Render PostgreSQL
export DATABASE_URL="postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/saveeat"

# 2. Chargez les données
python scripts/load_to_postgres.py
```

**Option B: Via Render Shell**

```bash
# 1. Render Dashboard → Web Service → Shell
# 2. Vérifiez que DATABASE_URL est défini
echo $DATABASE_URL

# 3. Chargez les données (les CSV doivent être dans data/raw/)
python main.py load-db --db-type postgresql
```

**Option C: Via script Python direct**

```python
import os
from scripts.load_to_postgres import load_to_postgres

# Définir DATABASE_URL
os.environ["DATABASE_URL"] = "postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/saveeat"

# Charger les données
load_to_postgres()
```

#### 4. Vérifier le Chargement

Dans le Render Shell ou localement:

```python
from src.api.database import Database, Recipe, Review

db = Database(database_type="postgresql", ...)  # Les params seront pris de DATABASE_URL
session = db.get_session()

print(f"Recettes: {session.query(Recipe).count()}")
print(f"Reviews: {session.query(Review).count()}")
session.close()
```

Vous devriez voir:
- Recettes: 522,517
- Reviews: 1,401,982

---

## Vérification et Tests

### 1. Vérifier les Logs

Render Dashboard → Votre Web Service → **"Logs"**

Recherchez ces messages:
```
INFO:src.api.main:Using SQLite database (default)
INFO:src.api.main:Database initialized with 522517 recipes
```

Ou pour PostgreSQL:
```
INFO:src.api.main:Using PostgreSQL from DATABASE_URL: dpg-xxxxx-a.oregon-postgres.render.com
INFO:src.api.main:Database initialized with 522517 recipes
```

### 2. Tester les Endpoints

```bash
# Health check
curl https://your-app.onrender.com/health

# Obtenir une recette
curl https://your-app.onrender.com/api/v1/recipe/38

# Obtenir des recommandations (exemple)
curl -X POST https://your-app.onrender.com/api/v1/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "available_ingredients": ["chicken", "tomato", "pasta"],
    "max_time": 30,
    "top_k": 10
  }'
```

### 3. Tester le Frontend

Accédez à `https://your-app.onrender.com` dans votre navigateur.

---

## Dépannage

### Problème: "Database is empty (0 recipes)"

**Causes possibles:**
1. Le fichier `data/saveeat.db` n'est pas présent (SQLite)
2. Les données ne sont pas chargées dans PostgreSQL
3. Le chemin de la base de données est incorrect

**Solutions:**
- SQLite: Uploadez `data/saveeat.db` (voir Option 1, Étape 2)
- PostgreSQL: Exécutez `python scripts/load_to_postgres.py` (voir Option 2, Étape 3)

### Problème: "Module not found" ou "Import Error"

**Cause:** Les dépendances ne sont pas installées correctement.

**Solution:**
1. Vérifiez `build.sh` s'exécute correctement
2. Vérifiez les logs de build
3. Vérifiez `requirements.txt` est complet

### Problème: "Connection refused" (PostgreSQL)

**Causes possibles:**
1. DATABASE_URL pointe vers `localhost` (❌ incorrect pour Render)
2. Utilisation de l'External URL au lieu de l'Internal URL
3. PostgreSQL n'est pas créé ou est dans une région différente

**Solutions:**
1. Utilisez l'**Internal Database URL** de Render
2. Format correct: `postgresql://user:pass@dpg-xxxxx-a.oregon-postgres.render.com:5432/saveeat`
3. Vérifiez que PostgreSQL et Web Service sont dans la même région

### Problème: Build trop long ou échoue

**Cause:** PyTorch avec CUDA est trop gros (2+ GB).

**Solution:** Le `build.sh` installe PyTorch CPU-only (~200 MB):
```bash
pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu
```

### Problème: "Disk quota exceeded"

**Cause:** Free plan limité à 512 MB de RAM.

**Solutions:**
1. Utilisez SQLite (plus léger que PostgreSQL)
2. Upgradez vers Starter plan ($7/mois)
3. Optimisez les imports (lazy loading)

### Problème: Application lente ou timeout

**Causes:**
1. Cold start (Free plan dort après inactivité)
2. Pas assez de mémoire

**Solutions:**
1. Utilisez Starter plan (pas de cold start)
2. Optimisez les requêtes de base de données
3. Ajoutez du caching

---

## 📊 Comparaison des Options

| Critère | SQLite | PostgreSQL |
|---------|--------|------------|
| Setup | ⚡ 5 minutes | 🕐 15 minutes |
| Configuration | ✅ Aucune | ⚙️ DATABASE_URL |
| Persistance | 📦 Fichier | ☁️ Cloud managé |
| Performance (lecture) | ⚡ Rapide | ⚡ Rapide |
| Performance (écriture) | 💾 Limitée | 💾 Excellente |
| Coût | 💰 Gratuit | 💰 Gratuit (90j) puis $7/mois |
| Recommandé pour | Démo, Projet | Production |

---

## 🎯 Recommandation Finale

**Pour ce projet académique (démo en décembre):**
- ✅ Utilisez **SQLite** (Option 1)
- Simple, rapide, aucune config
- Parfait pour la démonstration

**Si vous voulez montrer "production-ready":**
- ✅ Utilisez **PostgreSQL** (Option 2)
- Montre que vous maîtrisez les bases de données cloud
- Bonus points pour la démo technique

---

## 📞 Support

Si vous rencontrez des problèmes:
1. Vérifiez les logs Render: Dashboard → Logs
2. Testez en local d'abord: `python test_system.py`
3. Consultez la documentation Render: https://render.com/docs

---

**Créé par l'équipe Save Eat pour le projet RecSys Startup Sprint**

