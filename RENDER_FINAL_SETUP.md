# 🎯 Setup Final Render - Configuration Directe

## ✅ Configuration PostgreSQL dans le Code

La configuration PostgreSQL est maintenant **directement dans `config/config.yaml`** :

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

## 🚀 Pour Render : Une Seule Variable d'Environnement

Sur Render, vous devez **seulement** ajouter `DATABASE_URL` avec l'**Internal Database URL** de votre PostgreSQL Render.

### Étapes :

1. **Créer PostgreSQL sur Render** :
   - Render Dashboard → "New" → "PostgreSQL"
   - Name : `saveeat-db`
   - Region : **Oregon** (même région que votre web service)
   - Plan : **Free**

2. **Copier l'Internal Database URL** :
   - Allez sur votre PostgreSQL
   - Section "Connections"
   - Copiez l'**Internal Database URL**
   - Format : `postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/saveeat`

3. **Ajouter sur le Web Service** :
   - Web Service → Settings → Environment
   - Key : `DATABASE_URL`
   - Value : L'Internal Database URL copiée
   - Save

4. **Charger les Données** :
   ```bash
   # Via Render Shell
   python main.py load-db --db-type postgresql
   ```

## ✅ Comment ça Fonctionne

1. Si `DATABASE_URL` existe → Utilise PostgreSQL Render (automatique)
2. Sinon → Utilise la config de `config.yaml` (localhost pour local)
3. Si PostgreSQL échoue → Fallback sur SQLite

## 📝 Résumé

- **Config dans le code** : ✅ `config.yaml` contient la config PostgreSQL
- **Sur Render** : Ajoutez juste `DATABASE_URL` (une seule variable)
- **En local** : Fonctionne directement avec la config (localhost)

C'est tout ! 🎉

