# 🍳 Save Eat - Smart Recipe Recommendation System

## 📖 Project Description

Save Eat is an intelligent recipe recommendation system that helps users discover recipes based on available ingredients, time constraints, and dietary preferences. The system uses Graph Neural Networks (GNN) combined with text embeddings to provide personalized recommendations.

**Key Features:**
- Context-aware recommendations (ingredients, time, dietary preferences)
- Hybrid architecture combining GNN with text embeddings
- Interactive web interface
- 522,517 recipes and 1,401,982 user reviews

## 👥 Team Members

- **Victor Lestrade** - Project Lead (PL)
- **Matthieu Houette** - Data Engineer (DE)  
- **Hugo Fouan** - Lead ML Engineer (MLE-Core)
- **Basile Sorrel** - ML Engineer - Ops (MLE-Ops)
- **Wadih Ben Abdesselem** - Systems Engineer (SE)

## 🚀 Quick Start (10 minutes)

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

### 5. Open in your browser

```
http://localhost:8000
```

**That's it!** The application is now running with a pre-loaded database containing 522,517 recipes.

## 📚 API Documentation

Once the server is running, access the interactive API documentation at:

```
http://localhost:8000/docs
```

## 🎯 Main Features

### Web Interface
- Browse and search recipes
- Filter by ingredients, time, and dietary preferences
- View detailed recipe information
- Get personalized recommendations

### API Endpoints
- `GET /` - Web interface
- `GET /health` - Health check
- `POST /api/v1/recommend` - Get personalized recommendations
- `GET /api/v1/recipe/{id}` - Get recipe details
- `GET /api/v1/recipes/search` - Search recipes
- `GET /api/v1/ingredients` - Get available ingredients
- `POST /api/v1/log_interaction` - Log user interactions

## 🔧 Advanced Usage

### Re-train the Model (Optional)

The system works out-of-the-box with popularity-based recommendations. To train the GNN model for personalized recommendations:

```bash
python main.py train
```

**Note:** Training requires processed data and can take 1-2 hours depending on your hardware.

### Preprocess Data (Optional)

If you want to reprocess the data:

```bash
python main.py preprocess
```

### Access the Database

The application uses SQLite by default (`data/saveeat.db`). You can query it directly or switch to PostgreSQL by setting the `DATABASE_URL` environment variable.

## 📁 Project Structure

```
Project/
├── app.py                      # Main entry point
├── main.py                     # CLI for advanced operations
├── requirements.txt            # Python dependencies
├── config/
│   └── config.yaml            # Configuration file
├── data/
│   ├── raw/                   # Raw dataset files
│   ├── processed/             # Preprocessed data
│   └── saveeat.db             # SQLite database (pre-loaded)
├── src/
│   ├── api/                   # FastAPI application
│   │   ├── main.py           # FastAPI app definition
│   │   ├── endpoints.py      # API endpoints
│   │   └── database.py       # Database models
│   ├── data/                  # Data processing
│   │   ├── loader.py         # Data loading
│   │   ├── preprocessing.py  # Data preprocessing
│   │   └── graph_builder.py  # Graph construction
│   ├── models/                # ML models
│   │   ├── gnn_model.py      # GNN architecture
│   │   ├── text_encoder.py   # Text embeddings
│   │   └── reranker.py       # Context-based re-ranking
│   └── training/              # Training pipeline
│       ├── train.py          # Training loop
│       └── evaluation.py     # Evaluation metrics
└── frontend/
    ├── index.html            # Web interface
    └── static/
        └── app.js            # Frontend logic
```

## 🛠️ Technology Stack

- **Backend:** Python 3.10+, FastAPI
- **ML Framework:** PyTorch, PyTorch Geometric
- **NLP:** Transformers (Sentence-BERT)
- **Frontend:** HTML5, JavaScript, Tailwind CSS
- **Database:** SQLite (default) / PostgreSQL (production)
- **Data:** Food.com dataset (Kaggle)

## 📊 Dataset

- **Source:** Food.com Recipes and Reviews (Kaggle)
- **Recipes:** 522,517 recipes with ingredients, instructions, and nutrition info
- **Reviews:** 1,401,982 user reviews and ratings
- **Pre-processed:** Data is already loaded in `data/saveeat.db`

## 🧪 Testing

The system includes comprehensive testing:

```bash
# Test the full system
python -c "from src.api.main import app; print('✅ App loads successfully')"

# Test API endpoints
curl http://localhost:8000/health

# Test recipe retrieval
curl http://localhost:8000/api/v1/recipe/38
```

## 🌐 Deployment

### Local Deployment (Recommended for Demo)

The application runs perfectly on localhost. To access from other devices on the same network:

```bash
python app.py
# Access from other devices: http://YOUR_LOCAL_IP:8000
```

### Cloud Deployment (Render)

The project is configured for deployment on Render:

1. Connect your GitHub repository to Render
2. Create a Web Service
3. Render will automatically use `build.sh` and `start.sh`
4. (Optional) Set `DATABASE_URL` for PostgreSQL

## 🔍 Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or change the port in app.py
```

### Dependencies Installation Fails

If PyTorch installation fails, install it separately:

```bash
# For CPU only
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Database Issues

The database is pre-loaded in `data/saveeat.db`. If you encounter issues:

```bash
# Verify database exists
ls -lh data/saveeat.db

# Should show: ~145 MB file
```

## 📝 Configuration

Main configuration is in `config/config.yaml`:

- Model hyperparameters (GNN layers, dimensions, dropout)
- Training parameters (batch size, learning rate, epochs)
- Database settings (SQLite/PostgreSQL)
- API configuration (host, port)

## 🎓 Academic Project

This project is part of the "RecSys Startup Sprint" course at ECE Paris.

**Innovation:** Hybrid GNN architecture combining collaborative filtering with content-based filtering using text embeddings and context-aware re-ranking.

**Evaluation Metrics:**
- NDCG@10 (Normalized Discounted Cumulative Gain)
- Recall@20
- MRR (Mean Reciprocal Rank)

## 📄 License

This project is for academic purposes.

## 🙏 Acknowledgments

- Food.com dataset from Kaggle
- PyTorch Geometric for GNN implementation
- Sentence-Transformers for text embeddings

---

**For questions or issues, please contact the team members.**

**Enjoy discovering new recipes! 🍳**
