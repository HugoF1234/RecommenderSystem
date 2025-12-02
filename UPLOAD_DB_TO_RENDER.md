# Guide : Uploader la Base de Données sur Render

## ✅ Données chargées localement

Votre base de données SQLite est maintenant remplie avec :
- **522,517 recettes**
- **1,401,982 reviews**

## 📦 Taille de la base de données

La base de données `data/saveeat.db` fait environ **~500-800 MB** (selon les données).

## 🚀 Méthode 1 : Upload via Render Shell (Recommandé)

### Étape 1 : Compresser la base de données

```bash
# Compresser la DB (réduit la taille de ~70%)
gzip -c data/saveeat.db > data/saveeat.db.gz

# Vérifier la taille
ls -lh data/saveeat.db.gz
```

### Étape 2 : Uploader via Render Shell

1. **Ouvrez Render Shell** :
   - Render Dashboard → Votre Web Service → "Shell"

2. **Créez le dossier data** :
   ```bash
   mkdir -p data
   ```

3. **Uploader depuis votre machine locale** :
   ```bash
   # Depuis votre terminal local
   # Remplacez <service-name> par le nom de votre service Render
   render shell <service-name>
   
   # OU utilisez scp/rsync si disponible
   # (Render ne supporte pas directement scp, donc utilisez l'interface web)
   ```

4. **Alternative : Utiliser l'interface Render** :
   - Render Dashboard → Votre service → "Shell"
   - Utilisez l'option "Upload File" si disponible
   - Ou copiez-collez via l'éditeur de fichiers

5. **Décompresser sur Render** :
   ```bash
   # Dans Render Shell
   cd /opt/render/project/src
   gunzip data/saveeat.db.gz
   ```

## 🚀 Méthode 2 : Utiliser un service de stockage (Google Drive, Dropbox)

### Étape 1 : Uploader la DB compressée

1. Compressez : `gzip -c data/saveeat.db > data/saveeat.db.gz`
2. Uploader sur Google Drive / Dropbox / etc.
3. Notez le lien de téléchargement

### Étape 2 : Télécharger sur Render

Modifiez `build.sh` pour télécharger automatiquement :

```bash
# Ajouter à la fin de build.sh
if [ ! -f "data/saveeat.db" ]; then
    echo "=== Downloading database ==="
    # Remplacez par votre lien
    wget -O data/saveeat.db.gz "https://your-link.com/saveeat.db.gz"
    gunzip data/saveeat.db.gz
fi
```

## 🚀 Méthode 3 : Utiliser PostgreSQL (Meilleure solution long terme)

Au lieu d'uploader SQLite, utilisez PostgreSQL sur Render :

1. **Créer PostgreSQL sur Render** (gratuit)
2. **Charger les données depuis votre machine** :
   ```bash
   python scripts/load_to_postgres.py \
     --host <render-postgres-host> \
     --database <db-name> \
     --user <user> \
     --password <password>
   ```

Voir `POSTGRESQL_SETUP.md` pour plus de détails.

## ⚡ Solution Rapide pour la Démo

### Option A : Uploader la DB compressée

1. **Compresser** :
   ```bash
   gzip -c data/saveeat.db > data/saveeat.db.gz
   ```

2. **Uploader via Render Shell** :
   - Ouvrez Render Shell
   - Utilisez l'option d'upload de fichiers
   - Décompressez : `gunzip data/saveeat.db.gz`

### Option B : Utiliser PostgreSQL (Recommandé)

1. Créez PostgreSQL sur Render
2. Chargez les données :
   ```bash
   python scripts/load_to_postgres.py --host ... --database ... --user ... --password ...
   ```

## 🔍 Vérification

Après upload, vérifiez dans les logs Render :

```
INFO:src.api.main:Database has 522517 recipes
```

## ⚠️ Notes Importantes

- **SQLite sur Render** : Les données peuvent être perdues lors des redéploiements (sauf si vous utilisez un volume persistant)
- **PostgreSQL** : Les données sont persistantes et plus fiables
- **Taille** : La DB compressée fait ~150-250 MB (plus facile à uploader)

## 🎯 Recommandation

Pour la production, utilisez **PostgreSQL** plutôt que SQLite. C'est plus robuste et les données sont garanties de persister.

