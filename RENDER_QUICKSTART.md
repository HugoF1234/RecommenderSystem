# 🚀 Déploiement Rapide sur Render (5 minutes)

## ✅ Prérequis

Vous avez déjà tout ce qu'il faut :
- ✅ Base de données SQLite avec 522,517 recettes (data/saveeat.db)
- ✅ Scripts de build et démarrage configurés
- ✅ Code testé et fonctionnel

## 📝 Étapes de Déploiement

### 1. Créer le Web Service (2 minutes)

1. Allez sur [Render Dashboard](https://dashboard.render.com/)
2. **New** → **Web Service**
3. Connectez votre repository GitHub
4. Configuration:
   ```
   Name: saveeat-api
   Region: Oregon
   Branch: main
   Runtime: Python 3
   Build Command: chmod +x build.sh && ./build.sh
   Start Command: chmod +x start.sh && ./start.sh
   Instance Type: Free (ou Starter pour meilleures performances)
   ```
5. **Create Web Service**

### 2. Uploader la Base de Données (3 minutes)

**La base de données SQLite n'est PAS dans Git (fichier trop gros).**

Vous devez l'uploader manuellement sur Render:

#### Option A: Via Render Shell (Recommandé)

1. Render Dashboard → Votre Web Service → **Shell**
2. Dans le shell:
   ```bash
   mkdir -p data
   # Puis uploadez data/saveeat.db via l'interface Render
   ```

#### Option B: Commiter la base (si < 100 MB après compression)

```bash
# Compresser
gzip -c data/saveeat.db > data/saveeat.db.gz

# Retirer de .gitignore
# (Éditez .gitignore, retirez *.db)

# Commiter
git add data/saveeat.db.gz
git commit -m "Add compressed database"
git push

# Modifier build.sh pour décompresser:
echo "gunzip -f data/saveeat.db.gz" >> build.sh
```

#### Option C: Utiliser Render Disk (Persistant)

1. Render Dashboard → **Disks** → **New Disk**
   - Name: `saveeat-data`
   - Size: 1 GB
   - Mount Path: `/opt/render/project/src/data`
2. Attachez le disk à votre web service
3. Uploadez saveeat.db via Shell dans `/opt/render/project/src/data/`

### 3. Vérifier le Déploiement

1. Attendez la fin du build (3-5 minutes)
2. Testez:
   ```bash
   # Health check
   curl https://your-app.onrender.com/health
   
   # Get recipe
   curl https://your-app.onrender.com/api/v1/recipe/38
   ```
3. Ouvrez le frontend: `https://your-app.onrender.com`

## ✅ C'est Tout !

Votre application est déployée avec SQLite !

## 🔧 Alternative: PostgreSQL (Optionnel)

Si vous préférez PostgreSQL (recommandé pour production):

1. **Créer PostgreSQL** sur Render:
   - New → PostgreSQL
   - Name: `saveeat-db`
   - Region: Oregon (même que web service)
   - Plan: Free

2. **Configurer DATABASE_URL**:
   - Web Service → Environment
   - Ajoutez: `DATABASE_URL` = `<Internal Database URL from PostgreSQL>`

3. **Charger les données** (depuis votre machine):
   ```bash
   export DATABASE_URL="<External Connection String from Render>"
   python scripts/load_to_postgres.py
   ```

## 📊 Comparaison

| Méthode | Setup | Avantages |
|---------|-------|-----------|
| **SQLite** | 5 min | Simple, gratuit, aucune config |
| **PostgreSQL** | 15 min | Meilleur pour production, données backupées |

**Pour la démo du projet:** SQLite suffit amplement !

## 🐛 Problèmes Courants

### "Database is empty"
→ La base de données n'a pas été uploadée sur Render  
→ Suivez l'Étape 2

### "Module not found"
→ Le build a échoué  
→ Vérifiez les logs de build dans Render

### Application lente
→ Cold start du plan Free (dort après inactivité)  
→ Upgradez vers Starter ($7/mois) ou attendez 30-60s au premier accès

## 📞 Support

- Logs: Render Dashboard → Votre Web Service → Logs
- Documentation complète: `RENDER_DEPLOYMENT_GUIDE.md`
- Tests: `python diagnose_render.py`

---

**Bon déploiement ! 🚀**

