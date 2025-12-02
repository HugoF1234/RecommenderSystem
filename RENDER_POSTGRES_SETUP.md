# 🚀 Setup Complet Render + PostgreSQL

## ✅ Étape 1 : Créer PostgreSQL sur Render

1. Allez sur https://dashboard.render.com
2. Cliquez sur **"New"** → **"PostgreSQL"**
3. Configurez :
   - **Name** : `saveeat-db`
   - **Database** : `saveeat` (ou laissez par défaut)
   - **User** : (généré automatiquement)
   - **Region** : **Oregon** (même région que votre web service)
   - **Plan** : **Free** (pour commencer)
4. Cliquez sur **"Create Database"**

## ✅ Étape 2 : Configurer les Variables d'Environnement

1. Allez sur votre **Web Service** sur Render
2. **Settings** → **Environment**
3. Ajoutez **UNE SEULE** variable :

   **Key** : `DATABASE_URL`
   
   **Value** : Copiez l'**Internal Database URL** de votre PostgreSQL
   
   Format : `postgresql://user:password@host:port/database`
   
   Exemple : `postgresql://saveeat_user:abc123@dpg-xxxxx-a/saveeat`

4. Cliquez sur **"Save Changes"**

## ✅ Étape 3 : Charger les Données

### Option A : Depuis votre machine locale (Recommandé)

1. **Récupérez l'External Connection String** de votre PostgreSQL sur Render
2. **Depuis votre terminal local**, exécutez :

```bash
python scripts/load_to_postgres.py \
  --host <host-from-external-connection> \
  --port 5432 \
  --database <database-name> \
  --user <user-from-external-connection> \
  --password <password-from-external-connection>
```

**OU** utilisez directement l'External Connection String :

```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
python scripts/load_to_postgres.py
```

### Option B : Via Render Shell

1. Ouvrez **Render Shell** pour votre web service
2. Exécutez :

```bash
# Les variables d'environnement sont déjà configurées
python main.py load-db --db-type postgresql
```

## ✅ Étape 4 : Vérifier

Après le déploiement, vérifiez les logs Render. Vous devriez voir :

```
INFO:src.api.main:Using PostgreSQL from DATABASE_URL: dpg-xxxxx-a
INFO:src.api.main:Database has 522517 recipes
```

## 📋 Checklist Complète

- [ ] PostgreSQL créé sur Render
- [ ] Variable `DATABASE_URL` ajoutée au Web Service
- [ ] Données chargées dans PostgreSQL
- [ ] Web Service redéployé
- [ ] Logs montrent "Database has X recipes"

## 🎯 Variables d'Environnement sur Render

**UNE SEULE variable nécessaire** :

```
DATABASE_URL=postgresql://user:password@host:port/database
```

C'est tout ! Le code détecte automatiquement cette variable et se connecte.

## 🔧 Si ça ne fonctionne pas

1. **Vérifiez les logs** : Cherchez les erreurs de connexion
2. **Vérifiez DATABASE_URL** : Doit être l'**Internal Database URL** (pas External)
3. **Vérifiez la région** : Web Service et PostgreSQL doivent être dans la même région
4. **Vérifiez que les données sont chargées** : Exécutez le script de chargement

## 📝 Notes Importantes

- **Internal Database URL** : Pour connexion depuis Render (votre web service)
- **External Connection String** : Pour connexion depuis votre machine locale
- Les données sont **persistantes** : Elles survivent aux redéploiements
- **Free tier** : 90 jours de rétention, 256 MB de stockage

