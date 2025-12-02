# 🚀 Déploiement Ultra-Simple sur Render

## ✅ Solution la Plus Simple : SQLite (Aucune Config !)

**Pas besoin de variables d'environnement, pas besoin de PostgreSQL !**

## 📋 Étapes (2 minutes)

### 1️⃣ Charger les Données Localement

```bash
# Charge les données dans SQLite (déjà fait !)
python main.py load-db
```

Cela crée `data/saveeat.db` avec toutes les données.

### 2️⃣ Uploader la Base de Données sur Render

**Option A : Via Render Shell (Recommandé)**

1. Render Dashboard → Votre Web Service → **"Shell"**
2. Créez le dossier :
   ```bash
   mkdir -p data
   ```
3. **Uploader le fichier** `data/saveeat.db` :
   - Utilisez l'interface Render pour uploader le fichier
   - Ou utilisez `scp` depuis votre machine :
   ```bash
   # Depuis votre machine locale
   scp data/saveeat.db <render-user>@<render-host>:~/data/
   ```

**Option B : Compresser et Uploader**

```bash
# Compresser (réduit à ~40-50 MB)
gzip -c data/saveeat.db > data/saveeat.db.gz

# Uploader data/saveeat.db.gz sur Render
# Puis dans Render Shell :
gunzip data/saveeat.db.gz
```

### 3️⃣ C'est Tout !

L'application utilise automatiquement SQLite, **aucune variable d'environnement nécessaire** !

## ✅ Avantages

- ✅ **Aucune config** : Pas de variables d'environnement
- ✅ **Fonctionne partout** : Local, Render, Heroku, etc.
- ✅ **Simple** : Juste uploader un fichier
- ✅ **Rapide** : SQLite est très performant pour la lecture

## ⚠️ Note

SQLite sur Render :
- Les données **persistent** entre les redéploiements (le fichier reste)
- Si vous supprimez le service, les données sont perdues
- Pour la production à long terme, PostgreSQL est mieux

## 🎯 Pour la Démo

**C'est parfait !** SQLite fonctionne très bien pour une démo.

## 📝 Alternative : PostgreSQL (Optionnel)

Si vous voulez PostgreSQL plus tard :
1. Créez PostgreSQL sur Render
2. Ajoutez `DATABASE_URL` dans les variables d'environnement
3. L'app utilisera automatiquement PostgreSQL

Mais pour commencer, **SQLite est plus simple** !

