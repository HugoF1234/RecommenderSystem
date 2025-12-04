# 🍳 Save Eat - Smart Recipe Recommendation System

## 📖 Project Description

Save Eat is an intelligent recipe recommendation system that helps users discover recipes based on available ingredients, time constraints, and dietary preferences. The system uses **Graph Neural Networks (GNN)** combined with **text embeddings** to provide personalized recommendations.

**Key Features:**
- 🧠 **Graph Neural Networks (GAT)** - State-of-the-art collaborative filtering
- 📝 **Text Encoder** - Content-based recommendations using transformers
- 🎯 **Context-Aware Reranker** - Personalization based on ingredients, time, preferences
- 👤 **User Profiles** - Dietary restrictions, allergies, nutritional preferences
- 🌐 **Web Interface** - Beautiful, modern UI with real-time recommendations

**Dataset:**
- 94,496 recipes
- 1,401,982 user reviews
- 27,657 active users

## 👥 Team Members

- **Victor Lestrade** - Project Lead (PL)
- **Matthieu Houette** - Data Engineer (DE)  
- **Hugo Fouan** - Lead ML Engineer (MLE-Core)
- **Basile Sorrel** - ML Engineer - Ops (MLE-Ops)
- **Wadih Ben Abdesselem** - Systems Engineer (SE)

---

## 🚀 Quick Start (5 Steps)

### 1. Clone the repository

```bash
git clone https://github.com/HugoF1234/RecommenderSystem.git
cd RecommenderSystem
```

### 2. Create a virtual environment

```bash
# macOS/Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

### 5. Open your browser

Navigate to: **http://localhost:8000**

The API documentation is available at: **http://localhost:8000/docs**

---

## 📁 Project Structure

```
Project/
├── 📄 app.py                          # Main entry point (local execution)
├── 📄 main.py                         # CLI interface (preprocess, train, etc.)
├── 📄 start.sh                        # Startup script for Render
├── 📄 build.sh                        # Build script for Render
│
├── 📁 config/
│   └── config.yaml                    # Configuration file (model, training, API)
│
├── 📁 data/
│   ├── raw/                           # Raw data (CSV files from Kaggle)
│   │   ├── recipes.csv                # Recipe data
│   │   └── reviews.csv                # User reviews/ratings
│   │
│   ├── processed/                     # Processed data (created by preprocessing)
│   │   ├── mappings.pkl              # User/recipe index mappings
│   │   ├── recipes.csv                # Processed recipes with features
│   │   ├── graph.pt                   # PyTorch Geometric graph
│   │   ├── train.csv                  # Training interactions
│   │   ├── val.csv                    # Validation interactions
│   │   └── test.csv                   # Test interactions
│   │
│   ├── saveeat.db                     # SQLite database (local)
│   └── saveeat.db.gz                  # Compressed database (for Git)
│
├── 📁 src/
│   ├── api/                           # FastAPI backend
│   │   ├── main.py                    # FastAPI app initialization
│   │   ├── endpoints.py               # API endpoints (recommend, profile, etc.)
│   │   └── database.py                # Database models and operations
│   │
│   ├── models/                        # ML models
│   │   ├── gnn_model.py               # HybridGNN (GAT + Text Encoder)
│   │   ├── text_encoder.py            # Sentence transformers for content
│   │   └── reranker.py                # Contextual reranker (MLP)
│   │
│   ├── data/                          # Data processing
│   │   ├── loader.py                  # Load CSV files
│   │   ├── preprocessing.py           # Data preprocessing pipeline
│   │   ├── graph_builder.py           # Build PyTorch Geometric graphs
│   │   ├── db_to_processed.py         # Load from database → processed files
│   │   └── load_to_db.py              # Load CSV → database
│   │
│   └── training/                      # Training pipeline
│       ├── train.py                   # Training loop
│       └── evaluation.py              # Metrics (NDCG, Recall, MRR)
│
├── 📁 frontend/                       # Web interface
│   ├── index.html                     # Main HTML page
│   └── static/
│       ├── app.js                     # Frontend JavaScript
│       ├── LogoSaveEat.png           # Logo
│       └── fond/                      # Background images
│
├── 📁 scripts/                        # Utility scripts
│   ├── load_to_postgres.py           # Load data to PostgreSQL
│   └── setup_postgres_local.sh       # PostgreSQL setup
│
└── 📁 models/                         # Trained models (created after training)
    └── checkpoints/
        └── best_model.pt              # Best model checkpoint
```

---

## 🔧 Technologies Used

### Backend
- **FastAPI** - Modern Python web framework
- **PyTorch** - Deep learning framework
- **PyTorch Geometric** - Graph neural networks
- **SQLAlchemy** - Database ORM
- **PostgreSQL/SQLite** - Database

### ML Models
- **HybridGNN** - Graph Attention Networks (GAT) with multi-head attention
- **Text Encoder** - Sentence-transformers (all-MiniLM-L6-v2)
- **Contextual Reranker** - MLP for context-aware re-ranking

### Frontend
- **HTML5** - Structure
- **JavaScript** - Interactivity
- **Tailwind CSS** - Styling

---

## 📊 Data Flow

```
1. Raw Data (CSV)
   ↓
2. Database (SQLite/PostgreSQL)
   ↓
3. Preprocessing (python main.py preprocess)
   ├── Filter users/recipes
   ├── Extract features
   ├── Create mappings
   └── Build graph
   ↓
4. Processed Files
   ├── mappings.pkl
   ├── recipes.csv
   ├── graph.pt
   └── train/val/test.csv
   ↓
5. Model Training (python main.py train)
   └── best_model.pt
   ↓
6. API Server (python app.py)
   ├── Load model
   ├── Load graph
   └── Serve recommendations
```

---

## 🎯 Model Architecture

### HybridGNN
- **Input**: Heterogeneous graph (users, recipes, ingredients)
- **Architecture**: 
  - Graph Attention Networks (GAT) with 4 attention heads
  - Text encoder for recipe descriptions
  - Multi-layer aggregation
- **Output**: User and recipe embeddings

### Contextual Reranker
- **Input**: Base GNN scores + context features
- **Features**: 
  - Ingredient overlap
  - Time constraints
  - Dietary preferences
- **Architecture**: MLP (256 → 128 → 64)

---

## 🛠️ Commands

### Preprocess Data
```bash
python main.py preprocess
```
Loads data from database and creates processed files (mappings, graph, recipes).

### Train Model
```bash
python main.py train
```
Trains the GNN model and saves checkpoint to `models/checkpoints/best_model.pt`.

### Run API
```bash
python app.py
```
Starts the FastAPI server on http://localhost:8000

### Load Data to Database
```bash
python main.py load-db
```
Loads CSV files into SQLite database.

---

## 📝 API Endpoints

### Recommendations
- `POST /api/v1/recommend` - Get recipe recommendations
- `GET /api/v1/recipe/{recipe_id}` - Get recipe details
- `GET /api/v1/ingredients` - Get available ingredients

### User Profile
- `POST /api/v1/user/{user_id}/profile` - Create/update profile
- `GET /api/v1/user/{user_id}/profile` - Get user profile
- `PATCH /api/v1/user/{user_id}/profile` - Update profile

### Interactions
- `POST /api/v1/log` - Log user interaction (view, click, rate)

---

## 🔍 How It Works

### 1. Model Loading (Startup)
- Loads mappings, graph, and recipes from `data/processed/`
- Initializes GNN model (with or without trained weights)
- Initializes reranker
- All services ready for recommendations

### 2. Recommendation Flow
```
User Request
    ↓
Get User Embedding (GNN)
    ↓
Compute Scores (dot product with all recipes)
    ↓
Contextual Reranking (if context provided)
    ↓
Filter by User Profile (allergies, restrictions)
    ↓
Return Top-K Recommendations
```

### 3. Services Used
- ✅ **GNN (HybridGNN)** - Generates embeddings
- ✅ **Text Encoder** - Content-based features (integrated in GNN)
- ✅ **Reranker** - Context-aware re-ranking
- ✅ **Graph Builder** - Graph structure loaded

---

## 📈 Model Training

To train the model for better performance:

```bash
python main.py train
```

This will:
1. Load processed data
2. Build graph
3. Train GNN for multiple epochs
4. Save best model to `models/checkpoints/best_model.pt`

**Note**: Without training, the model uses random weights (low performance but functional).

---

## 🐛 Troubleshooting

### Model Not Loading
**Problem**: "Model not loaded, using fallback recommendations"

**Solution**:
1. Run preprocessing: `python main.py preprocess`
2. Verify files exist: `ls -la data/processed/`
3. Restart API: `python app.py`

### Missing Data Files
**Problem**: "Interactions file not found"

**Solution**: 
- Data is loaded from database, not CSV files
- Run: `python main.py preprocess` (loads from DB automatically)

### Port Already in Use
**Problem**: Port 8000 already in use

**Solution**: 
- Kill process: `kill -9 $(lsof -ti:8000)`
- Or use different port: `uvicorn app:app --port 8001`

---

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (when server is running)
- **Project Description**: `project_description (1).ipynb`
- **Technology Analysis**: `ANALYSE_TECHNOLOGIES_RECSYS.md`
- **Implementation Guide**: `IMPLEMENTATION_MODEL_LOADING.md`

---

## 🎓 Academic Context

This project is part of the **RecSys Startup Sprint** course. The system implements:
- Advanced GNN architecture (GAT)
- Hybrid recommendation system
- Context-aware recommendations
- Full-stack deployment

**Evaluation Metrics:**
- NDCG@10
- Recall@20
- MRR (Mean Reciprocal Rank)

---

## 📄 License

This project is for educational purposes.

---

## 🙏 Acknowledgments

- Dataset: Food.com Recipes and Reviews (Kaggle)
- PyTorch Geometric team
- FastAPI developers

---

**Made with ❤️ by the Save Eat Team**
