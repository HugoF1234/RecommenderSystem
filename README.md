# 🍳 Save Eat - Recommandation de Recettes Intelligentes

Save Eat est un système de recommandation de recettes basé sur des Graph Neural Networks (GNN) qui transforme les ingrédients disponibles en suggestions personnalisées et intelligentes.

## 📋 Table des Matières

- [Description du Projet](#description-du-projet)
- [Équipe](#équipe)
- [Architecture Technique](#architecture-technique)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Structure du Projet](#structure-du-projet)
- [Documentation Technique](#documentation-technique)

## 📖 Description du Projet

Save Eat adresse le défi quotidien des étudiants et jeunes professionnels : "Qu'est-ce que je peux cuisiner avec ce que j'ai ?". Le système combine :

- **Recommandation personnalisée** basée sur l'historique utilisateur
- **Awareness contextuelle** (ingrédients disponibles, temps disponible, préférences alimentaires)
- **Architecture hybride GNN** fusionnant graphes de relations recette-ingrédient avec embeddings textuels
- **Re-ranking contextuel** pour optimiser les suggestions en temps réel

### Innovation Technique

1. **Graph Neural Networks** : Modélisation des relations utilisateurs-recettes-ingrédients via PyTorch Geometric
2. **Embeddings textuels** : Fusion des caractéristiques textuelles (titres, descriptions) avec Transformers
3. **Re-ranking contextuel** : Réorganisation intelligente basée sur les contraintes réelles (ingrédients, temps, préférences)

## 👥 Équipe

- **Project Lead (PL)** : Victor Lestrade
- **Data Engineer (DE)** : Matthieu Houette
- **Lead ML Engineer (MLE-Core)** : Hugo Fouan
- **ML Engineer - Ops (MLE-Ops)** : Basile Sorrel
- **Systems Engineer (SE)** : Wadih Ben Abdesselem

## 🏗️ Architecture Technique

### Stack Technologique

- **Backend** : Python 3.10+, FastAPI
- **ML Framework** : PyTorch, PyTorch Geometric
- **NLP** : Transformers (Hugging Face)
- **Frontend** : HTML5, JavaScript, Tailwind CSS
- **Database** : PostgreSQL / SQLite
- **Data** : Food.com Cleaned Dataset (Kaggle - RecSys project dataset Food.com)

### Architecture en 3 Couches

1. **Data Layer** : Ingestion, nettoyage, construction de graphes
2. **Recommendation Layer** : Modèle GNN hybride + re-ranking
3. **Serving Layer** : API FastAPI + Frontend Tailwind CSS

## 🚀 Installation et Lancement Rapide

**Temps estimé : 10 minutes**

### Prérequis

- Python 3.10 ou supérieur
- pip ou conda
- Git
- Compte Kaggle (pour télécharger le dataset)

### Guide d'Installation Étape par Étape

#### Étape 1 : Cloner le Repository

```bash
git clone https://github.com/HugoF1234/RecommenderSystem.git
cd RecommenderSystem
```

#### Étape 2 : Créer un Environnement Virtuel

```bash
# Option A : Avec venv (recommandé)
python -m venv venv
source venv/bin/activate  # Sur macOS/Linux
# ou sur Windows :
venv\Scripts\activate

# Option B : Avec conda
conda create -n saveeat python=3.10
conda activate saveeat
```

#### Étape 3 : Installer les Dépendances

```bash
pip install -r requirements.txt
```

**Note :** Si vous rencontrez des erreurs avec PyTorch, installez-le séparément selon votre système :
```bash
# Pour CPU uniquement
pip install torch torchvision torchaudio

# Pour GPU (CUDA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Étape 4 : Télécharger le Dataset

##### Option A : Avec l'API Kaggle (Automatique)

1. Configurez vos credentials Kaggle :
   - Créez un compte sur [Kaggle](https://www.kaggle.com/)
   - Téléchargez votre `kaggle.json` depuis Account > API
   - Placez-le dans `~/.kaggle/kaggle.json` (macOS/Linux) ou `C:\Users\<username>\.kaggle\kaggle.json` (Windows)

2. Téléchargez le dataset :
   ```bash
   python main.py download
   ```

##### Option B : Téléchargement Manuel

1. Allez sur Kaggle et recherchez **"RecSys project dataset Food.com"**
2. Téléchargez le dataset
3. Extrayez les fichiers **`reviews_clean_full.csv`** et **`recipes_clean_full.csv`** dans `data/raw/`
   
   **Note:** Le système utilise maintenant le dataset nettoyé pour de meilleurs résultats. Si les fichiers nettoyés ne sont pas disponibles, le système essaiera automatiquement de charger les fichiers originaux (`reviews.csv` et `recipes.csv`) en fallback.

#### Étape 5 : Préparer les Données

```bash
python main.py preprocess
```

Cela va nettoyer les données, extraire les caractéristiques et créer les fichiers nécessaires dans `data/processed/`.

**Temps estimé :** 2-5 minutes selon la taille du dataset.

#### Étape 6 : Lancer le Système

```bash
python main.py serve
```

Le serveur démarre sur `http://localhost:8000`

**C'est tout !** Vous pouvez maintenant ouvrir votre navigateur et accéder à :
- **Interface utilisateur :** http://localhost:8000
- **Documentation API :** http://localhost:8000/docs

## 💻 Utilisation

### Démarrer le Système

```bash
python main.py serve
```

L'API sera accessible sur `http://localhost:8000`

- **Frontend (Interface utilisateur) :** http://localhost:8000
- **Documentation API interactive :** http://localhost:8000/docs
- **Health check :** http://localhost:8000/health

### Utiliser le Frontend

1. Ouvrez votre navigateur
2. Accédez à `http://localhost:8000`
3. Sélectionnez vos ingrédients disponibles
4. Optionnel : Spécifiez un temps maximum (minutes)
5. Optionnel : Sélectionnez vos préférences alimentaires (Végétarien, Végan, Sans gluten, Sans lactose)
6. Cliquez sur "Chercher des Recettes"
7. Cliquez sur "Voir la recette" pour afficher les détails complets

### Tester l'API directement

```bash
# Exemple de requête de recommandation
curl -X POST "http://localhost:8000/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "available_ingredients": ["tomato", "pasta", "cheese"],
    "max_time": 30,
    "dietary_preferences": ["vegetarian"],
    "top_k": 10
  }'
```

### 4. Entraîner le Modèle (Optionnel)

Si vous souhaitez entraîner le modèle GNN depuis zéro :

```bash
python main.py train
```

**Note importante :** Le système fonctionne sans modèle entraîné en utilisant des recommandations basées sur la popularité et les ingrédients. L'entraînement du modèle GNN est optionnel mais recommandé pour obtenir des recommandations personnalisées.

**Pour entraîner le modèle manuellement** (si `python main.py train` n'est pas encore implémenté) :

1. Créez un script Python ou utilisez un notebook Jupyter :
```python
from src.data.loader import DataLoader
from src.data.preprocessing import DataPreprocessor
from src.data.graph_builder import GraphBuilder
from src.models.gnn_model import HybridGNN
from src.training.train import Trainer
import torch
import yaml
from pathlib import Path

# Load config
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Load processed data
loader = DataLoader()
data = loader.load_all()
preprocessor = DataPreprocessor()
processed_data = preprocessor.process(data["interactions"], data["recipes"])

# Build graph
graph_builder = GraphBuilder(embedding_dim=config["graph"]["embedding_dim"])
graph_data = graph_builder.build_hetero_graph(
    processed_data["train"],
    processed_data["recipes"],
    processed_data["mappings"]
)

# Initialize model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = HybridGNN(
    embedding_dim=config["graph"]["embedding_dim"],
    hidden_dim=config["model"]["gnn"]["hidden_dim"],
    num_layers=config["model"]["gnn"]["num_layers"],
    dropout=config["model"]["gnn"]["dropout"]
)
model.initialize_embeddings(
    processed_data["stats"]["n_users"],
    processed_data["stats"]["n_recipes"],
    device
)

# Train
trainer = Trainer(
    model=model,
    train_data=processed_data,
    val_data=processed_data,
    config=config["training"],
    device=device
)

history = trainer.train(
    graph_data=graph_data,
    save_path=Path(config["training"]["save_path"])
)
```

Le modèle entraîné sera sauvegardé dans `models/checkpoints/best_model.pt` et sera automatiquement chargé par l'API au prochain démarrage.

## 📁 Structure du Projet

```
Project/
├── README.md                      # Ce fichier
├── requirements.txt               # Dépendances Python
├── main.py                        # Point d'entrée principal (CLI)
├── config/
│   └── config.yaml                # Configuration (hyperparamètres, chemins)
├── data/
│   ├── raw/                       # Dataset brut (Food.com)
│   ├── processed/                 # Données préprocessées
│   └── saveeat.db                 # Base de données SQLite (créée automatiquement)
├── models/
│   └── checkpoints/               # Modèles entraînés (.pt)
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py              # Chargement du dataset
│   │   ├── preprocessing.py       # Préprocessing des données
│   │   └── graph_builder.py       # Construction du graphe
│   ├── models/
│   │   ├── __init__.py
│   │   ├── gnn_model.py           # Architecture GNN hybride
│   │   ├── text_encoder.py        # Encoder textuel (Transformers)
│   │   └── reranker.py            # Re-ranking contextuel
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py               # Boucle d'entraînement
│   │   └── evaluation.py          # Métriques (NDCG@10, Recall@20, MRR)
│   └── api/
│       ├── __init__.py
│       ├── main.py                # Application FastAPI
│       ├── endpoints.py           # Endpoints API
│       └── database.py              # Gestion base de données
├── frontend/
│   ├── index.html                 # Interface utilisateur
│   └── static/
│       └── app.js                 # Logique frontend
└── notebooks/
    └── exploration.ipynb          # Exploration des données
```

## 📚 Documentation Technique

### Endpoints API

#### POST `/api/v1/recommend`

Obtenir des recommandations de recettes pour un utilisateur.

**Body:**
```json
{
  "user_id": 1,
  "available_ingredients": ["tomate", "pâtes", "fromage"],
  "max_time": 30,
  "dietary_preferences": ["vegetarian"],
  "top_k": 10
}
```

**Response:**
```json
{
  "recipe_ids": [123, 456, 789, ...],
  "scores": [0.95, 0.89, 0.82, ...],
  "explanations": ["Recommandé: ...", ...]
}
```

#### POST `/api/v1/log_interaction`

Logger une interaction utilisateur-recette.

**Body:**
```json
{
  "user_id": 1,
  "recipe_id": 123,
  "interaction_type": "click",
  "rating": 4.5,
  "available_ingredients": ["tomate", "pâtes"]
}
```

#### GET `/api/v1/user/{user_id}/interactions`

Obtenir l'historique des interactions d'un utilisateur.

### Métriques d'Évaluation

- **NDCG@10** : Normalized Discounted Cumulative Gain à 10
- **Recall@20** : Rappel à 20 recommandations
- **MRR** : Mean Reciprocal Rank

### Configuration

Les hyperparamètres sont configurables dans `config/config.yaml` :

- Paramètres du modèle GNN
- Paramètres d'entraînement (batch size, learning rate, etc.)
- Paramètres de la base de données
- Paramètres de l'API

## ✅ Vérification Rapide

Pour vérifier que tout fonctionne correctement :

```bash
# 1. Vérifier que Python est installé
python --version  # Doit être 3.10+

# 2. Vérifier que les dépendances sont installées
pip list | grep torch
pip list | grep fastapi

# 3. Vérifier que les données sont préprocessées
ls data/processed/train.csv data/processed/recipes.csv

# 4. Tester le serveur
python main.py serve
# Dans un autre terminal :
curl http://localhost:8000/health
# Devrait retourner : {"status":"healthy"}
```

## 🐛 Dépannage

### L'API ne démarre pas

- Vérifiez que le port 8000 n'est pas utilisé : `lsof -i :8000` (macOS/Linux)
- Vérifiez que toutes les dépendances sont installées : `pip list`

### Le modèle n'est pas trouvé

- Le modèle doit être entraîné d'abord ou téléchargé
- Vérifiez que `models/checkpoints/best_model.pt` existe
- L'API fonctionnera sans modèle mais les recommandations ne fonctionneront pas

### Erreur de dataset

- Vérifiez que les fichiers sont dans `data/raw/`
- Vérifiez les noms de fichiers (peuvent varier selon la version du dataset)

## 🚀 Déploiement

### Déploiement Local (Recommandé pour la démo)

Le système fonctionne parfaitement en local. Pour permettre l'accès depuis d'autres machines sur le même réseau :

1. Démarrez le serveur avec l'option `--host 0.0.0.0` :
```bash
python main.py serve --host 0.0.0.0
```

2. Trouvez l'adresse IP locale de votre machine :
```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig
```

3. Accédez depuis une autre machine sur le même réseau WiFi :
```
http://VOTRE_IP_LOCALE:8000
```

### Déploiement Cloud (Optionnel)

Pour un déploiement cloud, plusieurs options sont disponibles :

#### Google Cloud Run (Recommandé - Free Tier généreux)

1. Créez un `Dockerfile` :
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

2. Déployez avec Cloud Run :
```bash
gcloud run deploy saveeat --source . --platform managed
```

#### Heroku (Alternative simple)

1. Créez un `Procfile` :
```
web: python main.py serve --host 0.0.0.0 --port $PORT
```

2. Déployez :
```bash
heroku create saveeat
git push heroku main
```

**Note :** Le déploiement cloud est optionnel. Un déploiement local fonctionnel est parfaitement acceptable pour ce projet.

## 📊 Résumé des Commandes

```bash
# Télécharger le dataset
python main.py download

# Préprocesser les données
python main.py preprocess

# Entraîner le modèle (optionnel)
python main.py train

# Lancer le serveur
python main.py serve

# Lancer avec rechargement automatique (développement)
python main.py serve --reload

# Voir toutes les commandes
python main.py --help
```

## ⚡ Quick Start (Résumé Ultra-Rapide)

Pour les personnes pressées qui veulent lancer le projet en 10 minutes :

```bash
# 1. Installation
git clone https://github.com/HugoF1234/RecommenderSystem.git
cd RecommenderSystem
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Données (si pas déjà fait)
python main.py download && python main.py preprocess

# 3. Lancer
python main.py serve
# Ouvrir http://localhost:8000
```

**C'est tout !** Le système est maintenant accessible.

---

**Note** : Ce projet est réalisé dans le cadre du cours "RecSys Startup Sprint" par l'équipe Save Eat.

