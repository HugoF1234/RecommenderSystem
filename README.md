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
- **Data** : Food.com Dataset (Kaggle)

### Architecture en 3 Couches

1. **Data Layer** : Ingestion, nettoyage, construction de graphes
2. **Recommendation Layer** : Modèle GNN hybride + re-ranking
3. **Serving Layer** : API FastAPI + Frontend Tailwind CSS

## 🚀 Installation

### Prérequis

- Python 3.10 ou supérieur
- pip ou conda
- Git

### Étapes d'Installation

#### 1. Cloner le Repository

```bash
git clone https://github.com/HugoF1234/RecommenderSystem.git
cd RecommenderSystem
```

#### 2. Créer un Environnement Virtuel

```bash
# Avec venv
python -m venv venv
source venv/bin/activate  # Sur macOS/Linux
# ou
venv\Scripts\activate  # Sur Windows

# Avec conda
conda create -n saveeat python=3.10
conda activate saveeat
```

#### 3. Installer les Dépendances

```bash
pip install -r requirements.txt
```

#### 4. Télécharger le Dataset

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

1. Allez sur [Food.com Dataset](https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews)
2. Téléchargez le dataset
3. Extrayez les fichiers `reviews.csv` et `recipes.csv` dans `data/raw/`

#### 5. Préparer les Données

```bash
python main.py preprocess
```

Cela va nettoyer les données, extraire les caractéristiques et créer les fichiers nécessaires dans `data/processed/`.

## 💻 Utilisation

### 1. Démarrer l'API Backend et le Frontend

```bash
python main.py serve
```

L'API sera accessible sur `http://localhost:8000`

- Documentation interactive : `http://localhost:8000/docs`
- Frontend : `http://localhost:8000/`

### 2. Utiliser le Frontend

1. Ouvrez votre navigateur
2. Accédez à `http://localhost:8000`
3. Sélectionnez vos ingrédients disponibles
4. Optionnel : Spécifiez un temps maximum (minutes)
5. Optionnel : Sélectionnez vos préférences alimentaires (Végétarien, Végan, Sans gluten, Sans lactose)
6. Cliquez sur "Chercher des Recettes"
7. Cliquez sur "Voir la recette" pour afficher les détails complets

### 3. Tester l'API directement

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

Si vous souhaitez entraîner le modèle depuis zéro :

```bash
python main.py train
```

## 📁 Structure du Projet

```
Project/
├── README.md                      # Ce fichier
├── requirements.txt               # Dépendances Python
├── main.py                        # Point d'entrée principal (à développer)
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

## 🔮 Fonctionnalités Futures

- [ ] Reconnaissance d'ingrédients par image
- [ ] Apprentissage par renforcement pour la personnalisation continue
- [ ] Interaction vocale
- [ ] Intégration avec des APIs de courses
- [ ] Mode hors-ligne pour mobile

## 📄 Licence

Ce projet est réalisé dans le cadre du cours "RecSys Startup Sprint".

## 📞 Contact

Pour toute question, contactez l'équipe Save Eat.

---

**Note** : Ce projet est en développement actif. N'hésitez pas à contribuer !
