# Guide de Déploiement sur Render

## 📋 Fichiers Créés pour Render

1. **`app.py`** : Point d'entrée pour gunicorn
2. **`render.yaml`** : Configuration Render
3. **`runtime.txt`** : Version Python
4. **`requirements.txt`** : Mis à jour avec gunicorn

## 🚀 Commandes Git pour Push sur GitHub

### 1. Vérifier l'état actuel

```bash
# Voir les fichiers modifiés
git status

# Voir les différences
git diff
```

### 2. Ajouter tous les fichiers

```bash
# Ajouter tous les nouveaux fichiers et modifications
git add .

# Ou ajouter spécifiquement les fichiers de déploiement
git add app.py render.yaml runtime.txt requirements.txt
git add src/ config/ frontend/ README.md
```

### 3. Commit les changements

```bash
# Créer un commit avec un message descriptif
git commit -m "Add Render deployment configuration

- Add app.py for gunicorn entry point
- Add render.yaml for Render service configuration
- Add runtime.txt for Python version
- Update requirements.txt with gunicorn
- Improve GNN model with GAT (Graph Attention Networks)
- Add technical improvements documentation"
```

### 4. Push sur GitHub

```bash
# Si vous êtes sur la branche main
git push origin main

# Si vous êtes sur une autre branche et voulez push sur main
git push origin HEAD:main

# Ou si vous voulez créer/updater la branche main
git checkout -b main  # Si vous n'êtes pas déjà sur main
git push -u origin main
```

### 5. Vérifier que tout est bien pushé

```bash
# Voir les dernières commits
git log --oneline -5

# Vérifier la branche distante
git branch -r
```

## 🔧 Configuration Render

### Sur le Dashboard Render

1. **Connecter le Repository GitHub**
   - Allez sur https://dashboard.render.com
   - Cliquez sur "New" → "Web Service"
   - Connectez votre repository GitHub
   - Sélectionnez la branche `main`

2. **Configuration Automatique**
   - Render détectera automatiquement le `render.yaml`
   - Ou configurez manuellement :
     - **Build Command** : `pip install -r requirements.txt`
     - **Start Command** : `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --worker-class uvicorn.workers.UvicornWorker`
     - **Environment** : Python 3
     - **Plan** : Starter (ou Free pour tester)

3. **Variables d'Environnement (Optionnel)**
   - `PYTHON_VERSION=3.10.0`
   - `PORT=10000` (géré automatiquement par Render)

4. **Health Check**
   - Path : `/health`
   - Render vérifiera automatiquement que l'API répond

## ⚠️ Notes Importantes

### Données et Modèles

Les fichiers dans `data/` et `models/checkpoints/` sont dans `.gitignore` et ne seront **PAS** pushés sur GitHub.

**Options pour les données sur Render :**

1. **Option 1 : Upload manuel après déploiement**
   - Utilisez Render Shell pour uploader les fichiers
   - Ou utilisez un service de stockage (S3, etc.)

2. **Option 2 : Télécharger depuis Kaggle sur Render**
   - Ajoutez vos credentials Kaggle comme variables d'environnement
   - Exécutez `python main.py download` dans Render Shell

3. **Option 3 : Utiliser un volume persistant**
   - Render propose des volumes pour les données

### Pour le premier déploiement

Le système fonctionnera avec des recommandations de fallback (basées sur la popularité) si le modèle n'est pas présent. C'est acceptable pour la démo.

## 🧪 Tester Localement avec Gunicorn

Avant de push, testez localement que gunicorn fonctionne :

```bash
# Installer gunicorn si pas déjà fait
pip install gunicorn

# Tester avec gunicorn
gunicorn app:app --bind 0.0.0.0:8000 --workers 2 --timeout 120 --worker-class uvicorn.workers.UvicornWorker

# Ouvrir http://localhost:8000
```

## 📝 Checklist Avant Push

- [ ] `app.py` créé et testé
- [ ] `render.yaml` configuré
- [ ] `requirements.txt` mis à jour avec gunicorn
- [ ] `runtime.txt` présent
- [ ] Code testé localement
- [ ] `.gitignore` vérifié (pas de données sensibles)
- [ ] README.md à jour

## 🔗 URLs Après Déploiement

Une fois déployé, votre API sera accessible sur :
- **API** : `https://votre-service.onrender.com`
- **Health Check** : `https://votre-service.onrender.com/health`
- **Frontend** : `https://votre-service.onrender.com/`
- **API Docs** : `https://votre-service.onrender.com/docs`

