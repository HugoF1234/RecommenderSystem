# ⚡ Quick Start - Render + PostgreSQL

## 🎯 Objectif : Faire fonctionner l'app sur Render avec PostgreSQL

## 📋 Étapes (5 minutes)

### 1️⃣ Créer PostgreSQL sur Render

1. Render Dashboard → **"New"** → **"PostgreSQL"**
2. **Name** : `saveeat-db`
3. **Region** : **Oregon** (ou même région que votre web service)
4. **Plan** : **Free**
5. Cliquez **"Create Database"**

### 2️⃣ Configurer la Variable d'Environnement

1. Allez sur votre **Web Service**
2. **Settings** → **Environment**
3. Cliquez **"Add Environment Variable"**
4. **Key** : `DATABASE_URL`
5. **Value** : Copiez l'**Internal Database URL** de votre PostgreSQL
   - Format : `postgresql://user:password@host:port/database`
   - Exemple : `postgresql://saveeat_user:abc123xyz@dpg-xxxxx-a.oregon-postgres.render.com:5432/saveeat`
6. Cliquez **"Save Changes"**

### 3️⃣ Charger les Données

**Option A : Depuis votre machine (Recommandé)**

```bash
# Utilisez l'External Connection String de Render
export DATABASE_URL="postgresql://user:password@host:port/database"
python scripts/load_to_postgres.py
```

**Option B : Via Render Shell**

1. Render Dashboard → Votre Web Service → **"Shell"**
2. Exécutez :
```bash
python main.py load-db --db-type postgresql
```

### 4️⃣ Vérifier

Les logs Render devraient montrer :
```
INFO:src.api.main:Using PostgreSQL from DATABASE_URL: dpg-xxxxx-a
INFO:src.api.main:Database initialized with 522517 recipes
```

## ✅ C'est tout !

L'application fonctionne maintenant avec PostgreSQL sur Render.

## 🔍 Variables d'Environnement Requises

**UNE SEULE variable** :

```
DATABASE_URL=postgresql://user:password@host:port/database
```

Le code détecte automatiquement cette variable et se connecte à PostgreSQL.

## 🆘 Troubleshooting

**Erreur "connection refused"** :
- Vérifiez que vous utilisez l'**Internal Database URL** (pas External)
- Vérifiez que Web Service et PostgreSQL sont dans la même région

**Base de données vide** :
- Exécutez le script de chargement : `python main.py load-db --db-type postgresql`

**Pas de données** :
- Les données doivent être chargées manuellement (pas automatique pour éviter les timeouts)

