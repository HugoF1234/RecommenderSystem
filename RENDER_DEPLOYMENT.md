# Guide de Déploiement sur Render avec Base de Données

## 📋 Problème : Les CSV ne sont pas sur GitHub

C'est **normal** ! Les fichiers CSV sont dans `.gitignore` car ils sont trop volumineux (plusieurs centaines de MB) pour être versionnés sur GitHub.

## 🚀 Solutions pour Render

### Option 1 : Uploader les CSV via Render Shell (Recommandé)

1. **Connectez-vous à Render Shell** :
   - Allez sur votre service Render
   - Cliquez sur "Shell" dans le menu
   - Ou utilisez : `render shell <service-name>`

2. **Créez les dossiers** :
   ```bash
   mkdir -p data/raw
   ```

3. **Uploader les fichiers CSV** :
   - Utilisez `scp` ou `rsync` depuis votre machine locale :
   ```bash
   # Depuis votre machine locale
   scp data/raw/recipes_clean_full.csv <render-user>@<render-host>:~/data/raw/
   scp data/raw/reviews_clean_full.csv <render-user>@<render-host>:~/data/raw/
   ```
   
   **OU** utilisez l'interface Render pour uploader via le Shell

4. **Chargez les données dans la base de données** :
   ```bash
   python main.py load-db
   ```

### Option 2 : Télécharger depuis Kaggle sur Render

1. **Configurez Kaggle API sur Render** :
   - Dans Render Dashboard → Environment Variables
   - Ajoutez :
     - `KAGGLE_USERNAME` = votre username Kaggle
     - `KAGGLE_KEY` = votre API key Kaggle

2. **Créez un script de setup** :
   ```bash
   # Dans Render Shell
   python main.py download
   python main.py load-db
   ```

### Option 3 : Utiliser un Volume Persistant (Payant)

1. **Créez un Volume Persistant** sur Render
2. **Montez-le** dans votre service
3. **Stockez les CSV** dans le volume
4. **Chargez les données** une fois

### Option 4 : Utiliser un Service de Stockage (S3, etc.)

1. **Uploader les CSV** sur S3 ou un service similaire
2. **Télécharger** au démarrage de l'API
3. **Charger** dans la base de données

## 📝 Script Automatique pour Render

Créez un script qui s'exécute au build pour télécharger et charger les données :

```python
# scripts/setup_render.py
import os
from pathlib import Path
from src.data.loader import DataLoader
from src.data.load_to_db import load_data_to_database

def setup_render():
    """Setup data for Render deployment"""
    # Download from Kaggle if credentials are available
    if os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"):
        loader = DataLoader()
        try:
            loader.download_dataset("hugofouan/recsys-project-dataset-foodcom")
        except:
            print("Kaggle download failed, using manual upload")
    
    # Load into database
    load_data_to_db()
```

## ✅ Solution Recommandée pour la Démo

**Pour une démo rapide** :

1. **Localement** : Chargez les données dans la base de données
   ```bash
   python main.py load-db
   ```

2. **Uploader la base de données** sur Render :
   ```bash
   # La base de données SQLite sera dans data/saveeat.db
   # Uploader ce fichier sur Render via Shell
   ```

3. **OU** : Utilisez un service de stockage cloud (Google Drive, Dropbox) et téléchargez au démarrage

## 🔧 Modification du Build pour Render

Vous pouvez modifier `build.sh` pour télécharger automatiquement :

```bash
#!/bin/bash
# Build script for Render deployment

set -e

echo "=== Upgrading pip ==="
pip install --upgrade pip setuptools wheel

echo "=== Installing PyTorch CPU ==="
pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Setting up data (if available) ==="
# Try to load data if CSV files exist
if [ -f "data/raw/recipes_clean_full.csv" ] || [ -f "data/raw/recipes.csv" ]; then
    echo "CSV files found, loading into database..."
    python main.py load-db || echo "Data loading failed, will use empty database"
else
    echo "No CSV files found. Please upload data manually or use Kaggle API."
fi

echo "=== Build complete ==="
```

## 📌 Note Importante

- La base de données SQLite (`data/saveeat.db`) est aussi dans `.gitignore`
- Sur Render, vous devrez soit :
  - Uploader la DB pré-chargée
  - OU charger les données via `load-db` après le déploiement
  - OU utiliser PostgreSQL (service séparé sur Render)

## 🎯 Pour la Démo

**Solution la plus simple** :
1. Chargez les données localement : `python main.py load-db`
2. Uploader `data/saveeat.db` sur Render via Shell
3. L'API utilisera directement la base de données pré-chargée

