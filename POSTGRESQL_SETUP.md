# Guide PostgreSQL pour Save Eat

## 🎯 Pourquoi PostgreSQL ?

- **Meilleur pour la production** : Plus robuste et scalable que SQLite
- **Gratuit sur Render** : Service PostgreSQL gratuit disponible
- **Persistant** : Les données ne sont pas perdues au redéploiement
- **Performance** : Meilleures performances pour les requêtes complexes

## 📋 Setup Local

### 1. Installer PostgreSQL

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Télécharger depuis https://www.postgresql.org/download/windows/

### 2. Créer la base de données

**Option A : Script automatique**
```bash
chmod +x scripts/setup_postgres_local.sh
./scripts/setup_postgres_local.sh
```

**Option B : Manuellement**
```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer la base de données et l'utilisateur
CREATE USER saveeat_user WITH PASSWORD 'saveeat_password';
CREATE DATABASE saveeat OWNER saveeat_user;
GRANT ALL PRIVILEGES ON DATABASE saveeat TO saveeat_user;
\q
```

### 3. Charger les données

```bash
# Avec les credentials par défaut
python main.py load-db --db-type postgresql

# Ou avec des credentials personnalisés
python main.py load-db --db-type postgresql \
  --host localhost \
  --port 5432 \
  --database saveeat \
  --user saveeat_user \
  --password saveeat_password
```

### 4. Configurer l'application

Modifiez `config/config.yaml` :
```yaml
database:
  type: "postgresql"
  postgresql:
    host: "localhost"
    port: 5432
    database: "saveeat"
    user: "saveeat_user"
    password: "saveeat_password"
```

## 🚀 Setup sur Render

### 1. Créer une base de données PostgreSQL sur Render

1. Allez sur https://dashboard.render.com
2. Cliquez sur "New" → "PostgreSQL"
3. Configurez :
   - **Name** : `saveeat-db`
   - **Database** : `saveeat` (ou laissez par défaut)
   - **User** : (généré automatiquement)
   - **Region** : Même région que votre web service
   - **Plan** : Free (pour commencer)

4. Notez les informations de connexion :
   - **Internal Database URL** : `postgresql://user:password@host:port/database`
   - **External Connection String** : Pour connexion depuis votre machine locale

### 2. Connecter votre Web Service à PostgreSQL

1. Allez sur votre Web Service
2. **Settings** → **Environment**
3. Ajoutez la variable :
   - **Key** : `DATABASE_URL`
   - **Value** : L'**Internal Database URL** de votre base PostgreSQL

### 3. Charger les données sur Render

**Option A : Depuis votre machine locale (via External Connection)**

```bash
# Utilisez l'External Connection String de Render
python scripts/load_to_postgres.py \
  --host <render-postgres-host> \
  --port 5432 \
  --database <database-name> \
  --user <user> \
  --password <password>
```

**Option B : Via Render Shell**

1. Ouvrez Render Shell pour votre web service
2. Exécutez :
```bash
# Les variables d'environnement sont déjà configurées
python main.py load-db --db-type postgresql
```

**Option C : Script de build automatique**

Modifiez `build.sh` pour charger automatiquement :
```bash
# À la fin de build.sh
if [ -n "$DATABASE_URL" ]; then
    echo "=== Loading data into PostgreSQL ==="
    python scripts/load_to_postgres.py || echo "Data loading skipped"
fi
```

## 🔧 Vérification

### Vérifier la connexion locale

```bash
psql -h localhost -U saveeat_user -d saveeat
```

### Vérifier les données

```python
from src.api.database import Database
db = Database(database_type="postgresql", host="localhost", ...)
session = db.get_session()
from src.api.database import Recipe
print(f"Recipes: {session.query(Recipe).count()}")
```

## 📝 Variables d'Environnement

L'application détecte automatiquement PostgreSQL via :

1. **`DATABASE_URL`** (priorité) : Format Render standard
   ```
   postgresql://user:password@host:port/database
   ```

2. **Variables individuelles** :
   - `POSTGRESQL_HOST`
   - `POSTGRESQL_PORT`
   - `POSTGRESQL_DATABASE`
   - `POSTGRESQL_USER`
   - `POSTGRESQL_PASSWORD`

3. **Config file** : `config/config.yaml`

## 🎯 Avantages sur Render

- ✅ **Persistance** : Les données survivent aux redéploiements
- ✅ **Backup automatique** : Render fait des backups réguliers
- ✅ **Scalabilité** : Facile d'upgrader le plan
- ✅ **Sécurité** : Connexion interne sécurisée
- ✅ **Monitoring** : Dashboard avec métriques

## 🔄 Migration depuis SQLite

Si vous avez déjà des données en SQLite :

```python
# Script de migration (à créer si nécessaire)
from src.api.database import Database

# Charger depuis SQLite
sqlite_db = Database(database_type="sqlite", sqlite_path="data/saveeat.db")
# ... exporter les données ...

# Charger dans PostgreSQL
postgres_db = Database(database_type="postgresql", ...)
# ... importer les données ...
```

## ⚠️ Notes Importantes

- **Free tier** : 90 jours de rétention, 256 MB de stockage
- **Internal URL** : Utilisez l'Internal Database URL pour la connexion depuis votre web service
- **External URL** : Utilisez l'External Connection String pour la connexion depuis votre machine locale
- **Sécurité** : Ne commitez jamais les mots de passe dans le code !

## 🆘 Troubleshooting

### Erreur de connexion

```bash
# Vérifier que PostgreSQL est en cours d'exécution
pg_isready -h localhost

# Vérifier les logs
tail -f /var/log/postgresql/postgresql-*.log
```

### Permission denied

```bash
# Vérifier les permissions
sudo -u postgres psql -c "\du"
```

### Timeout sur Render

- Vérifiez que vous utilisez l'**Internal Database URL**
- Vérifiez que le web service et la DB sont dans la même région

