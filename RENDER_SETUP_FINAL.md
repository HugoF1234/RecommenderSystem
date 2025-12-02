# 🎯 Setup Final Render - Instructions Complètes

## ⚠️ Problème Actuel

Votre `DATABASE_URL` pointe vers `localhost`, ce qui ne fonctionne **PAS** sur Render.

Sur Render, vous devez utiliser l'**Internal Database URL** de votre PostgreSQL Render.

## ✅ Solution : 3 Étapes Simples

### Étape 1 : Créer PostgreSQL sur Render

1. Render Dashboard → **"New"** → **"PostgreSQL"**
2. **Name** : `saveeat-db`
3. **Region** : **Oregon** (même région que votre web service)
4. **Plan** : **Free**
5. Cliquez **"Create Database"**

### Étape 2 : Configurer DATABASE_URL (IMPORTANT)

1. Allez sur votre **PostgreSQL** sur Render
2. Dans la section **"Connections"**, copiez l'**Internal Database URL**
   - Format : `postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/saveeat`
   - ⚠️ **PAS** `localhost` ! C'est l'host de Render !

3. Allez sur votre **Web Service**
4. **Settings** → **Environment**
5. Ajoutez/modifiez :
   - **Key** : `DATABASE_URL`
   - **Value** : L'**Internal Database URL** que vous avez copiée
6. Cliquez **"Save Changes"**

### Étape 3 : Charger les Données

**Option A : Depuis votre machine (Recommandé)**

1. Sur votre PostgreSQL Render, copiez l'**External Connection String**
2. Depuis votre terminal local :

```bash
# Utilisez l'External Connection String
export DATABASE_URL="postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/saveeat"
python scripts/load_to_postgres.py
```

**Option B : Via Render Shell**

1. Render Dashboard → Votre Web Service → **"Shell"**
2. Exécutez :

```bash
python main.py load-db --db-type postgresql
```

⚠️ **Note** : Les CSV doivent être uploadés sur Render pour cette méthode.

## 🔍 Vérification

Après le redéploiement, les logs devraient montrer :

```
INFO:src.api.main:Using PostgreSQL from DATABASE_URL: dpg-xxxxx-a.oregon-postgres.render.com
INFO:src.api.main:Database initialized with 522517 recipes
```

## 📋 Format DATABASE_URL Correct

❌ **FAUX** (ne fonctionne pas sur Render) :
```
postgresql://saveeat_user:saveeat_password@localhost:5432/saveeat
```

✅ **CORRECT** (pour Render) :
```
postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/saveeat
```

Où `dpg-xxxxx-a.oregon-postgres.render.com` est l'host fourni par Render.

## 🎯 Résumé

1. Créer PostgreSQL sur Render
2. Copier l'**Internal Database URL** (pas localhost !)
3. Mettre dans `DATABASE_URL` sur le Web Service
4. Charger les données
5. ✅ Ça fonctionne !

