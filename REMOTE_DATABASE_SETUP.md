# Guide : Utiliser une Base de Données Distante

## ✅ Vous avez raison !

La base de données **n'a pas besoin d'être sur Render**. Elle peut être :
- **En local** sur votre machine
- **Sur un autre serveur** (VPS, cloud, etc.)
- **Sur un service cloud** (AWS RDS, Google Cloud SQL, etc.)
- **Sur Render PostgreSQL** (mais ce n'est pas obligatoire)

L'application se connecte simplement via une **URL de connexion** et fait des **requêtes SQL** via SQLAlchemy.

## 🔌 Comment ça fonctionne

Le code utilise **SQLAlchemy** qui :
1. Se connecte à la base de données via une URL de connexion
2. Exécute des requêtes SQL automatiquement
3. Gère les sessions et transactions

### Exemple de connexion

```python
# Le code fait déjà ça dans database.py
database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(database_url)
# Toutes les requêtes SQL passent par cet engine
```

## 📋 Configuration

### Option 1 : Variables d'Environnement (Recommandé)

Sur Render, configurez ces variables :

```bash
POSTGRESQL_HOST=votre-serveur.com
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=saveeat
POSTGRESQL_USER=votre_user
POSTGRESQL_PASSWORD=votre_password
```

### Option 2 : URL de Connexion Complète

```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

### Option 3 : Fichier de Configuration

Modifiez `config/config.yaml` :

```yaml
database:
  type: "postgresql"
  postgresql:
    host: "votre-serveur.com"  # Peut être n'importe où !
    port: 5432
    database: "saveeat"
    user: "votre_user"
    password: "votre_password"
```

## 🏠 Cas d'Usage : Base de Données Locale

### Scénario : PostgreSQL en local, API sur Render

1. **Installez PostgreSQL en local** :
   ```bash
   brew install postgresql  # macOS
   brew services start postgresql
   ```

2. **Chargez les données localement** :
   ```bash
   python main.py load-db --db-type postgresql \
     --host localhost \
     --database saveeat \
     --user postgres \
     --password votre_password
   ```

3. **Ouvrez le port PostgreSQL** (pour que Render puisse se connecter) :
   ```bash
   # Modifiez postgresql.conf pour écouter sur toutes les interfaces
   # listen_addresses = '*'
   
   # Modifiez pg_hba.conf pour autoriser les connexions distantes
   # host    all    all    0.0.0.0/0    md5
   ```

4. **Configurez le firewall** pour ouvrir le port 5432

5. **Sur Render**, configurez :
   ```bash
   POSTGRESQL_HOST=votre-ip-publique
   POSTGRESQL_PORT=5432
   POSTGRESQL_DATABASE=saveeat
   POSTGRESQL_USER=postgres
   POSTGRESQL_PASSWORD=votre_password
   ```

⚠️ **Note de sécurité** : Exposer PostgreSQL directement sur Internet nécessite une configuration sécurisée (SSL, firewall, etc.)

## ☁️ Cas d'Usage : Base de Données Cloud

### Option A : AWS RDS

```bash
POSTGRESQL_HOST=your-db.xxxxx.us-east-1.rds.amazonaws.com
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=saveeat
POSTGRESQL_USER=admin
POSTGRESQL_PASSWORD=your_password
```

### Option B : Google Cloud SQL

```bash
POSTGRESQL_HOST=xxx.xxx.xxx.xxx  # IP publique
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=saveeat
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=your_password
```

### Option C : DigitalOcean, Heroku, etc.

Même principe : configurez juste l'URL de connexion !

## 🔍 Vérification

Le code fait déjà des requêtes SQL comme ça :

```python
# Dans database.py
session.query(Recipe).count()  # SELECT COUNT(*) FROM recipes
session.query(Recipe).filter(Recipe.recipe_id == id).first()  # SELECT * FROM recipes WHERE...
```

Toutes ces requêtes passent par la connexion configurée !

## 🎯 Solution Simple pour Vous

### Garder PostgreSQL en Local

1. **PostgreSQL en local** avec les données chargées ✅ (déjà fait !)

2. **Sur Render**, configurez les variables d'environnement pour pointer vers votre machine :
   ```bash
   POSTGRESQL_HOST=votre-ip-publique
   POSTGRESQL_PORT=5432
   POSTGRESQL_DATABASE=saveeat
   POSTGRESQL_USER=postgres
   POSTGRESQL_PASSWORD=votre_password
   ```

3. **Ouvrez le port 5432** sur votre routeur/firewall

4. **C'est tout !** L'API sur Render se connectera à votre DB locale

## 🔒 Sécurité

Pour la production, utilisez :
- **SSL/TLS** pour la connexion
- **Firewall** pour limiter les IPs autorisées
- **VPN** ou **tunnel SSH** pour une connexion sécurisée
- **Service cloud géré** (AWS RDS, etc.) qui gère la sécurité

## 📝 Exemple Complet

```python
# Le code fait déjà tout ça automatiquement !
# Il suffit de configurer l'URL de connexion

# Sur Render (variables d'environnement)
POSTGRESQL_HOST=db.example.com
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=saveeat
POSTGRESQL_USER=myuser
POSTGRESQL_PASSWORD=mypassword

# Le code dans main.py détecte automatiquement ces variables
# et se connecte à la base de données distante
# Toutes les requêtes SQL passent par cette connexion
```

## ✅ Résumé

- ✅ La base de données peut être **n'importe où**
- ✅ Le code fait déjà des **requêtes SQL** via SQLAlchemy
- ✅ Il suffit de configurer l'**URL de connexion**
- ✅ Pas besoin que la DB soit sur Render !

