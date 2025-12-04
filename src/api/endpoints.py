"""
API Endpoints for Save Eat
FastAPI endpoints for recommendations and logging
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import torch
import numpy as np
import json
import logging

from .database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class RecommendationRequest(BaseModel):
    """Request model for recommendations"""
    user_id: int
    available_ingredients: Optional[List[str]] = None
    max_time: Optional[float] = None  # minutes
    dietary_preferences: Optional[List[str]] = None
    top_k: int = 20
    use_profile: bool = True  # Utiliser le profil utilisateur par défaut


class InteractionLogRequest(BaseModel):
    """Request model for logging interactions"""
    user_id: int
    recipe_id: int
    interaction_type: str = "view"  # view, click, like, rate
    rating: Optional[float] = None
    review: Optional[str] = None
    available_ingredients: Optional[List[str]] = None
    session_id: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    recipe_ids: List[int]
    scores: List[float]
    explanations: Optional[List[str]] = None


class UserProfileRequest(BaseModel):
    """Request model for creating/updating user profile"""
    username: Optional[str] = None
    email: Optional[str] = None

    # Dietary preferences
    dietary_restrictions: Optional[List[str]] = None  # ["vegetarian", "vegan", "gluten-free", etc.]
    allergies: Optional[List[str]] = None  # ["nuts", "dairy", "eggs", etc.]

    # Cuisine and ingredient preferences
    favorite_cuisines: Optional[List[str]] = None  # ["italian", "mexican", "asian", etc.]
    disliked_ingredients: Optional[List[str]] = None
    favorite_ingredients: Optional[List[str]] = None

    # Nutritional constraints
    max_calories: Optional[float] = None
    min_protein: Optional[float] = None
    max_carbs: Optional[float] = None
    max_fat: Optional[float] = None

    # Cooking preferences
    max_prep_time: Optional[float] = None
    skill_level: Optional[str] = None  # "beginner", "intermediate", "advanced"

    # Taste preferences (0-10 scale)
    spice_tolerance: Optional[int] = None
    sweetness_preference: Optional[int] = None


class UserProfileResponse(BaseModel):
    """Response model for user profile"""
    user_id: int
    username: Optional[str] = None
    email: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    favorite_cuisines: Optional[List[str]] = None
    disliked_ingredients: Optional[List[str]] = None
    favorite_ingredients: Optional[List[str]] = None
    max_calories: Optional[float] = None
    min_protein: Optional[float] = None
    max_carbs: Optional[float] = None
    max_fat: Optional[float] = None
    max_prep_time: Optional[float] = None
    skill_level: Optional[str] = None
    spice_tolerance: Optional[int] = None
    sweetness_preference: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# Global model and data (will be initialized at startup)
model = None
graph_data = None
recipe_data = None
reranker = None
mappings = None


def initialize_model(model_path: Optional[str], graph_data_path: str, recipe_data_path: str, mappings_path: str):
    """Initialize model and data (called at startup)"""
    global model, graph_data, recipe_data, reranker, mappings
    
    import torch
    import pickle
    import pandas as pd
    from pathlib import Path
    import yaml
    import os
    
    logger.info("🚀 Initializing model and data...")
    
    try:
        # Load config for model parameters
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        config = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        
        model_config = config.get("model", {})
        gnn_config = model_config.get("gnn", {})
        text_config = model_config.get("text_encoder", {})
        reranker_config = model_config.get("reranker", {})
        graph_config = config.get("graph", {})
        training_config = config.get("training", {})
        
        # 1. Load mappings
        if not Path(mappings_path).exists():
            logger.warning(f"❌ Mappings file not found: {mappings_path}")
            logger.warning("   Model will not be loaded. Please run: python main.py preprocess")
            return
        
        with open(mappings_path, 'rb') as f:
            mappings = pickle.load(f)
        
        n_users = len(mappings.get("user_to_idx", {}))
        n_recipes = len(mappings.get("recipe_to_idx", {}))
        logger.info(f"✅ Loaded mappings: {n_users} users, {n_recipes} recipes")
        
        # 2. Load graph data
        if not Path(graph_data_path).exists():
            logger.warning(f"❌ Graph data file not found: {graph_data_path}")
            logger.warning("   Model will not be loaded. Please build graph first.")
            return
        
        # PyTorch 2.6+ requires weights_only=False for HeteroData objects
        try:
            graph_data = torch.load(graph_data_path, map_location="cpu", weights_only=False)
        except TypeError:
            # Fallback for older PyTorch versions
            graph_data = torch.load(graph_data_path, map_location="cpu")
        logger.info(f"✅ Loaded graph data")
        if hasattr(graph_data, 'num_nodes'):
            logger.info(f"   Graph nodes: {graph_data.num_nodes}")
        if hasattr(graph_data, 'num_edges'):
            logger.info(f"   Graph edges: {graph_data.num_edges}")
        
        # 3. Load recipe data
        if not Path(recipe_data_path).exists():
            logger.warning(f"❌ Recipe data file not found: {recipe_data_path}")
            logger.warning("   Model will not be loaded. Please run: python main.py preprocess")
            return
        
        recipe_data = pd.read_csv(recipe_data_path)
        logger.info(f"✅ Loaded recipe data: {len(recipe_data)} recipes")
        
        # 4. Determine device
        device_str = training_config.get("device", "cpu")
        if device_str == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, using CPU")
            device_str = "cpu"
        device = torch.device(device_str)
        logger.info(f"✅ Using device: {device}")
        
        # 5. Initialize GNN model
        embedding_dim = graph_config.get("embedding_dim", 128)
        hidden_dim = gnn_config.get("hidden_dim", 256)
        num_layers = gnn_config.get("num_layers", 2)
        dropout = gnn_config.get("dropout", 0.3)
        activation = gnn_config.get("activation", "relu")
        text_embedding_dim = text_config.get("embedding_dim", 384)
        
        from ..models.gnn_model import HybridGNN
        
        model = HybridGNN(
            embedding_dim=embedding_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            dropout=dropout,
            activation=activation,
            text_embedding_dim=text_embedding_dim,
            use_text_features=True
        )
        
        # Initialize embeddings
        model.initialize_embeddings(n_users, n_recipes, device)
        model = model.to(device)
        
        # Load trained weights if available
        if model_path and Path(model_path).exists():
            try:
                # PyTorch 2.6+ requires weights_only=False for state_dict
                try:
                    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
                except TypeError:
                    # Fallback for older PyTorch versions
                    checkpoint = torch.load(model_path, map_location=device)
                
                # Handle different checkpoint formats
                if isinstance(checkpoint, dict):
                    if 'model_state_dict' in checkpoint:
                        model.load_state_dict(checkpoint['model_state_dict'])
                        logger.info(f"✅ Loaded model weights from checkpoint (epoch {checkpoint.get('epoch', '?')})")
                    else:
                        # Assume it's a state_dict directly
                        model.load_state_dict(checkpoint)
                        logger.info(f"✅ Loaded model weights from {model_path}")
                else:
                    model.load_state_dict(checkpoint)
                    logger.info(f"✅ Loaded model weights from {model_path}")
            except Exception as e:
                logger.warning(f"⚠️  Could not load model weights: {e}")
                logger.warning("   Using random initialization (model will need training)")
        else:
            if model_path:
                logger.warning(f"⚠️  Model checkpoint not found: {model_path}")
            else:
                logger.info("ℹ️  No model checkpoint path provided")
            logger.warning("   Using random initialization (model will need training)")
            logger.warning("   To train: python main.py train")
        
        model.eval()
        logger.info("✅ GNN model initialized")
        
        # 6. Initialize reranker
        from ..models.reranker import ContextualReranker
        
        reranker = ContextualReranker(
            input_dim=embedding_dim,
            hidden_dims=reranker_config.get("hidden_dims", [256, 128, 64]),
            dropout=reranker_config.get("dropout", 0.2),
            context_dim=50
        )
        reranker = reranker.to(device)
        reranker.eval()
        logger.info("✅ Contextual reranker initialized")
        
        logger.info("🎉 Model initialization complete!")
        logger.info(f"   - GNN: {n_users} users × {n_recipes} recipes")
        logger.info(f"   - Device: {device}")
        logger.info(f"   - Model ready for recommendations")
        
    except Exception as e:
        logger.error(f"❌ Error initializing model: {e}", exc_info=True)
        # Reset globals on error
        model = None
        graph_data = None
        recipe_data = None
        reranker = None
        mappings = None
        logger.error("   Model will not be available. Using fallback recommendations.")


@router.get("/recipe/{recipe_id}")
async def get_recipe(recipe_id: int):
    """
    Get recipe details by ID from database
    
    Args:
        recipe_id: Recipe ID
        
    Returns:
        Recipe details
    """
    try:
        # Get database instance
        from .main import db_instance
        
        if db_instance is None:
            raise HTTPException(status_code=503, detail="Database not initialized")
        
        # Get recipe from database
        recipe = db_instance.get_recipe_by_id(recipe_id)
        
        if recipe is None:
            raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")
        
        return recipe
        
        # Load ingredients - try processed CSV first (faster), then raw CSV if needed
        ingredients = []
        
        # First try: RecipeIngredientParts from processed CSV (already loaded, much faster)
        if "RecipeIngredientParts" in recipe.index and pd.notna(recipe["RecipeIngredientParts"]):
            try:
                ing_val = str(recipe["RecipeIngredientParts"]).strip()
                import re
                
                # Handle R-style format: c("ing1", "ing2", ...)
                if ing_val.startswith("c("):
                    ing_val = ing_val[2:]
                if ing_val.endswith(")"):
                    ing_val = ing_val[:-1]
                
                # Extract all quoted strings
                parts_ingredients = re.findall(r'"([^"]+)"', ing_val)
                
                if len(parts_ingredients) > 0:
                    ingredients = parts_ingredients
                    logger.debug(f"Recipe {recipe_id}: Loaded {len(ingredients)} ingredients from processed CSV")
            except Exception as e:
                logger.warning(f"Error parsing RecipeIngredientParts from processed CSV for recipe {recipe_id}: {e}")
        
        # Fallback: Only load raw CSV if processed CSV didn't work (slower but more complete)
        if len(ingredients) == 0:
            raw_recipes_path = Path("data/raw/recipes.csv")
            if raw_recipes_path.exists():
                try:
                    # Optimize: only load RecipeId and RecipeIngredientParts columns (much faster)
                    raw_df = pd.read_csv(raw_recipes_path, usecols=["RecipeId", "RecipeIngredientParts"])
                    raw_recipe = raw_df[raw_df["RecipeId"] == recipe_id]
                    
                    if not raw_recipe.empty:
                        raw_recipe = raw_recipe.iloc[0]
                        if "RecipeIngredientParts" in raw_recipe.index and pd.notna(raw_recipe["RecipeIngredientParts"]):
                            try:
                                ing_val = str(raw_recipe["RecipeIngredientParts"]).strip()
                                import re
                                
                                if ing_val.startswith("c("):
                                    ing_val = ing_val[2:]
                                if ing_val.endswith(")"):
                                    ing_val = ing_val[:-1]
                                
                                parts_ingredients = re.findall(r'"([^"]+)"', ing_val)
                                
                                if len(parts_ingredients) > 0:
                                    ingredients = parts_ingredients
                                    logger.info(f"Recipe {recipe_id}: Loaded {len(ingredients)} ingredients from RAW CSV")
                            except Exception as e:
                                logger.warning(f"Error parsing RecipeIngredientParts from raw CSV for recipe {recipe_id}: {e}")
                except Exception as e:
                    logger.warning(f"Error loading from raw CSV for recipe {recipe_id}: {e}")
        
        # Fallback: Try ingredients_list if RecipeIngredientParts failed or not available
        if len(ingredients) == 0 and "ingredients_list" in recipe.index and pd.notna(recipe["ingredients_list"]):
            try:
                ing_val = recipe["ingredients_list"]
                
                # If already a list, use it
                if isinstance(ing_val, list):
                    ingredients = [str(ing) for ing in ing_val]
                # If string, try to parse it
                elif isinstance(ing_val, str):
                    ing_val = ing_val.strip()
                    
                    # Try ast.literal_eval first (handles Python list strings like "['a', 'b']")
                    try:
                        ingredients = ast.literal_eval(ing_val)
                        if isinstance(ingredients, list):
                            ingredients = [str(ing) for ing in ingredients]
                        else:
                            ingredients = []
                    except (ValueError, SyntaxError):
                        # If that fails, try json.loads
                        try:
                            ingredients = json.loads(ing_val)
                            if isinstance(ingredients, list):
                                ingredients = [str(ing) for ing in ingredients]
                            else:
                                ingredients = []
                        except (json.JSONDecodeError, ValueError):
                            # Last resort: try eval (handles some edge cases, less safe)
                            try:
                                ingredients = eval(ing_val)
                                if isinstance(ingredients, list):
                                    ingredients = [str(ing) for ing in ingredients]
                                else:
                                    ingredients = []
                            except:
                                logger.warning(f"Could not parse ingredients_list for recipe {recipe_id}")
                                ingredients = []
            except Exception as e:
                logger.warning(f"Error parsing ingredients_list for recipe {recipe_id}: {e}")
                ingredients = []
        
        # Ensure we have a list (even if empty)
        if not isinstance(ingredients, list):
            ingredients = []
        
        # Log if ingredients list is still empty after all attempts
        if len(ingredients) == 0:
            logger.warning(f"Recipe {recipe_id} has no ingredients after all parsing attempts. Available columns: {[c for c in recipe.index if 'ingredient' in c.lower()]}")
        else:
            logger.debug(f"Recipe {recipe_id}: Successfully parsed {len(ingredients)} ingredients")
        
        # Parse steps - handle multiple formats
        steps = []
        if "steps_list" in recipe and pd.notna(recipe["steps_list"]):
            try:
                steps_val = recipe["steps_list"]
                
                # If already a list, use it
                if isinstance(steps_val, list):
                    steps = steps_val
                # If string, try to parse it
                elif isinstance(steps_val, str):
                    steps_val = steps_val.strip()
                    # Try ast.literal_eval first (handles Python list strings)
                    try:
                        steps = ast.literal_eval(steps_val)
                        if not isinstance(steps, list):
                            steps = []
                    except (ValueError, SyntaxError):
                        # If that fails, try json.loads
                        try:
                            steps = json.loads(steps_val)
                            if not isinstance(steps, list):
                                steps = []
                        except (json.JSONDecodeError, ValueError):
                            # Last resort: try eval
                            try:
                                steps = eval(steps_val)
                                if not isinstance(steps, list):
                                    steps = []
                            except:
                                logger.warning(f"Could not parse steps for recipe {recipe_id}: {steps_val[:50]}")
                                steps = []
            except Exception as e:
                logger.warning(f"Error parsing steps for recipe {recipe_id}: {e}")
                steps = []
        
        # Parse image URL if available
        image_url = None
        if "image_url" in recipe and pd.notna(recipe["image_url"]):
            image_url = str(recipe["image_url"]).strip()
            if not image_url or image_url == "nan":
                image_url = None
        elif "images_list" in recipe and pd.notna(recipe["images_list"]):
            try:
                images_val = recipe["images_list"]
                if isinstance(images_val, list) and len(images_val) > 0:
                    image_url = str(images_val[0])
                elif isinstance(images_val, str):
                    images_val = images_val.strip()
                    try:
                        images_list = ast.literal_eval(images_val)
                        if isinstance(images_list, list) and len(images_list) > 0:
                            image_url = str(images_list[0])
                    except:
                        pass
            except:
                pass
        
        # Fallback: parse from raw Images column if image_url not found
        if not image_url and "Images" in recipe and pd.notna(recipe["Images"]):
            try:
                import re
                images_str = str(recipe["Images"]).strip()
                if images_str and images_str != "nan":
                    # Extract first URL from R-style list: c("url1", "url2", ...)
                    urls = re.findall(r'"(https?://[^"]+)"', images_str)
                    if urls:
                        image_url = urls[0]
            except:
                pass
        
        # Build response
        recipe_data = {
            "recipe_id": int(recipe["recipe_id"]),
            "name": recipe.get("Name", recipe.get("name", f"Recipe {recipe_id}")),
            "description": recipe.get("Description", recipe.get("description", "")),
            "prep_time": int(recipe.get("prep_time", 0)) if pd.notna(recipe.get("prep_time")) else 0,
            "ingredients": ingredients,
            "steps": steps,
            "calories": float(recipe.get("calories", 0)) if pd.notna(recipe.get("calories")) else 0,
            "protein": float(recipe.get("protein", 0)) if pd.notna(recipe.get("protein")) else 0,
            "carbohydrates": float(recipe.get("carbohydrates", 0)) if pd.notna(recipe.get("carbohydrates")) else 0,
            "total_fat": float(recipe.get("total_fat", 0)) if pd.notna(recipe.get("total_fat")) else 0,
            "image_url": image_url,
        }
        
        return recipe_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recipe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ingredients")
async def get_ingredients(limit: int = 500):
    """
    Get list of available ingredients from database (cached for performance)
    
    Args:
        limit: Maximum number of ingredients to return
        
    Returns:
        List of ingredients
    """
    try:
        # Get cached ingredients (pre-calculated at startup for instant response)
        try:
            from .main import _ingredients_cache
        except ImportError:
            _ingredients_cache = None
        
        # Use cache if available (instant!)
        if _ingredients_cache is not None:
            return {"ingredients": _ingredients_cache[:limit]}
        
        # Cache not ready yet (still loading in background)
        # Return empty list with helpful message instead of slow database query
        logger.info("Ingredients cache not ready yet (loading in background)")
        return {
            "ingredients": [], 
            "message": "Ingredients are loading... Please refresh in a few seconds.",
            "status": "loading"
        }
        
    except Exception as e:
        logger.error(f"Error getting ingredients: {e}", exc_info=True)
        return {"ingredients": [], "error": str(e)}


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend(
    request: RecommendationRequest
):
    """
    Get recipe recommendations for a user
    
    Args:
        request: Recommendation request
        
    Returns:
        Recommended recipes with scores
    """
    try:
        # Fallback: if model is not loaded, return popular recipes based on simple heuristics
        if model is None or graph_data is None or recipe_data is None or mappings is None:
            logger.warning("Model not loaded, using fallback recommendations")
            return await _get_fallback_recommendations(request)
        # Get user embedding
        user_idx = mappings["user_to_idx"].get(request.user_id)
        if user_idx is None:
            # Cold start: use fallback recommendations (popular recipes)
            logger.info(f"User {request.user_id} not in mappings (cold start), using fallback recommendations")
            return await _get_fallback_recommendations(request)
        
        # Get base recommendations from GNN
        logger.info(f"🔍 Getting GNN recommendations for user {request.user_id} (idx: {user_idx})")
        model.eval()
        with torch.no_grad():
            # Move graph data to same device as model
            device = next(model.parameters()).device
            graph_data_device = graph_data.to(device)
            
            # Forward pass through GNN
            embeddings = model(graph_data_device)
            
            user_emb = embeddings["user_embeddings"][user_idx]
            recipe_embs = embeddings["recipe_embeddings"]
            
            # Compute scores (dot product)
            scores = torch.matmul(user_emb.unsqueeze(0), recipe_embs.T).squeeze().cpu().numpy()
            logger.info(f"✅ Computed scores for {len(scores)} recipes (min: {scores.min():.4f}, max: {scores.max():.4f}, mean: {scores.mean():.4f})")
        
        # Re-rank if contextual information provided
        if request.available_ingredients or request.max_time or request.dietary_preferences:
            if reranker is not None:
                # Prepare context features for each recipe
                top_k_indices = np.argsort(scores)[::-1][:request.top_k * 2]
                
                context_features = []
                reranked_scores = []
                
                for recipe_idx in top_k_indices:
                    recipe_id = mappings["idx_to_recipe"][recipe_idx]
                    recipe = recipe_data[recipe_data["recipe_id"] == recipe_id].iloc[0]
                    
                    # Get recipe ingredients (handle different formats)
                    recipe_ingredients = recipe.get("ingredients_list", [])
                    if isinstance(recipe_ingredients, str):
                        import ast
                        try:
                            recipe_ingredients = ast.literal_eval(recipe_ingredients)
                        except:
                            recipe_ingredients = []
                    if not isinstance(recipe_ingredients, list):
                        recipe_ingredients = []
                    
                    prep_time = recipe.get("minutes", recipe.get("prep_time", 30))
                    import pandas as pd
                    if pd.isna(prep_time):
                        prep_time = 30
                    
                    context = reranker.encode_context(
                        available_ingredients=request.available_ingredients or [],
                        recipe_ingredients=recipe_ingredients,
                        prep_time=float(prep_time),
                        max_time=request.max_time,
                        dietary_preferences=request.dietary_preferences
                    )
                    context_features.append(context)
                    reranked_scores.append(scores[recipe_idx])
                
                if context_features:
                    # Move to device
                    device = next(reranker.parameters()).device
                    context_tensor = torch.stack(context_features).to(device)
                    scores_tensor = torch.tensor(reranked_scores, dtype=torch.float32).to(device)
                    
                    reranked_scores = reranker.forward(scores_tensor, context_tensor).cpu().numpy()
                    
                    # Get top-k after re-ranking
                    top_indices = np.argsort(reranked_scores)[::-1][:request.top_k]
                    top_recipe_indices = top_k_indices[top_indices]
                else:
                    top_recipe_indices = np.argsort(scores)[::-1][:request.top_k]
            else:
                top_recipe_indices = np.argsort(scores)[::-1][:request.top_k]
        else:
            top_recipe_indices = np.argsort(scores)[::-1][:request.top_k]
        
        # Convert to recipe IDs
        recipe_ids = [mappings["idx_to_recipe"][idx] for idx in top_recipe_indices]
        final_scores = scores[top_recipe_indices].tolist()
        
        logger.info(f"✅ GNN selected {len(recipe_ids)} top recipes")
        
        # Apply user profile filters if requested (after GNN scoring)
        if request.use_profile and len(recipe_ids) > 0:
            try:
                from .main import db_instance
                if db_instance:
                    user_profile = db_instance.get_user_profile(request.user_id)
                    if user_profile:
                        logger.info(f"🔍 Applying profile filters to {len(recipe_ids)} GNN recommendations...")
                        # Filter recipe_ids based on profile (allergies only - most critical)
                        filtered_recipe_ids = []
                        filtered_scores = []
                        
                        for recipe_id, score in zip(recipe_ids, final_scores):
                            recipe = recipe_data[recipe_data["recipe_id"] == recipe_id]
                            if not recipe.empty:
                                recipe_row = recipe.iloc[0]
                                should_include = True
                                
                                # Check allergies only (safety critical)
                                if user_profile.get('allergies'):
                                    recipe_ingredients = recipe_row.get("ingredients_list", [])
                                    if isinstance(recipe_ingredients, str):
                                        import ast
                                        try:
                                            recipe_ingredients = ast.literal_eval(recipe_ingredients)
                                        except:
                                            recipe_ingredients = []
                                    if not isinstance(recipe_ingredients, list):
                                        recipe_ingredients = []
                                    
                                    for allergen in user_profile['allergies']:
                                        allergen_lower = allergen.lower().strip()
                                        for ing in recipe_ingredients:
                                            if allergen_lower in str(ing).lower():
                                                should_include = False
                                                break
                                        if not should_include:
                                            break
                                
                                if should_include:
                                    filtered_recipe_ids.append(recipe_id)
                                    filtered_scores.append(score)
                        
                        if len(filtered_recipe_ids) > 0:
                            logger.info(f"✅ After allergy filter: {len(filtered_recipe_ids)} recipes")
                            recipe_ids = filtered_recipe_ids
                            final_scores = filtered_scores
                        else:
                            logger.warning("⚠️  All recipes filtered out by allergies, returning top GNN recommendations anyway")
            except Exception as e:
                logger.warning(f"Error applying profile filters: {e}, returning GNN recommendations")
        
        # Generate explanations
        explanations = []
        for recipe_id in recipe_ids:
            recipe = recipe_data[recipe_data["recipe_id"] == recipe_id]
            if not recipe.empty:
                recipe_row = recipe.iloc[0]
                name = recipe_row.get("name", recipe_row.get("Name", f"Recipe {recipe_id}"))
                explanations.append(f"Recommended: {name}")
        
        if len(recipe_ids) == 0:
            logger.warning("⚠️  No recipes from GNN, falling back to popular recipes")
            return await _get_fallback_recommendations(request)
        
        logger.info(f"🎉 Returning {len(recipe_ids)} recommendations from GNN")
        return RecommendationResponse(
            recipe_ids=recipe_ids,
            scores=final_scores,
            explanations=explanations
        )
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def filter_recipes_by_allergies(recipes_df, allergies: List[str]):
    """
    Filtre les recettes contenant des allergènes

    Args:
        recipes_df: DataFrame de recettes
        allergies: List[str] - Liste d'allergènes (ex: ["nuts", "dairy", "eggs"])

    Returns:
        DataFrame filtré (sans les recettes contenant des allergènes)
    """
    import pandas as pd

    if not allergies or len(allergies) == 0:
        logger.debug("No allergies to filter")
        return recipes_df

    # Normaliser les allergènes pour la comparaison
    allergies_normalized = [a.lower().strip() for a in allergies]
    logger.info(f"Filtering recipes by allergies: {allergies_normalized}")

    def has_allergen(ingredients_list) -> bool:
        """Vérifie si la recette contient un allergène"""
        if not ingredients_list or not isinstance(ingredients_list, list):
            return False

        for ingredient in ingredients_list:
            if not ingredient:
                continue

            ing_lower = str(ingredient).lower().strip()

            # Vérifier si un allergène est présent dans l'ingrédient
            for allergen in allergies_normalized:
                if allergen in ing_lower:
                    logger.debug(f"Found allergen '{allergen}' in ingredient '{ingredient}'")
                    return True

        return False

    # Appliquer le filtre
    initial_count = len(recipes_df)
    recipes_df = recipes_df.copy()
    recipes_df['_has_allergen'] = recipes_df['ingredients_list'].apply(has_allergen)
    filtered_df = recipes_df[~recipes_df['_has_allergen']].drop(columns=['_has_allergen'])

    filtered_count = len(filtered_df)
    removed_count = initial_count - filtered_count

    logger.info(f"Allergy filter: removed {removed_count} recipes ({initial_count} → {filtered_count})")

    return filtered_df


def filter_recipes_by_dietary_restrictions(recipes_df, restrictions: List[str]):
    """
    Filtre les recettes selon les restrictions alimentaires

    Args:
        recipes_df: DataFrame de recettes
        restrictions: List[str] - Restrictions alimentaires (ex: ["vegetarian", "vegan", "gluten-free", "dairy-free"])

    Returns:
        DataFrame filtré (sans les recettes contenant des ingrédients interdits)
    """
    import pandas as pd

    if not restrictions or len(restrictions) == 0:
        logger.debug("No dietary restrictions to filter")
        return recipes_df

    # Normaliser les restrictions
    restrictions_normalized = [r.lower().strip() for r in restrictions]
    logger.info(f"Filtering recipes by dietary restrictions: {restrictions_normalized}")

    # Définir les ingrédients interdits par type de restriction
    RESTRICTED_INGREDIENTS = {
        'vegetarian': ['beef', 'pork', 'chicken', 'fish', 'meat', 'turkey', 'lamb', 'veal', 'duck', 'bacon', 'ham', 'sausage', 'seafood', 'shrimp', 'salmon', 'tuna'],
        'vegan': ['beef', 'pork', 'chicken', 'fish', 'meat', 'turkey', 'lamb', 'veal', 'duck', 'bacon', 'ham', 'sausage',
                  'dairy', 'milk', 'cheese', 'egg', 'butter', 'cream', 'yogurt', 'whey', 'casein', 'honey',
                  'gelatin', 'seafood', 'shrimp', 'salmon', 'tuna'],
        'gluten-free': ['wheat', 'flour', 'bread', 'pasta', 'gluten', 'barley', 'rye', 'oat', 'cereal', 'couscous', 'semolina'],
        'dairy-free': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'dairy', 'whey', 'casein', 'lactose'],
        'low-sugar': [],  # Géré par les filtres nutritionnels
        'high-protein': []  # Géré par les filtres nutritionnels
    }

    # Collecter tous les ingrédients interdits pour les restrictions spécifiées
    forbidden_ingredients = set()
    for restriction in restrictions_normalized:
        if restriction in RESTRICTED_INGREDIENTS:
            forbidden_ingredients.update(RESTRICTED_INGREDIENTS[restriction])
            logger.debug(f"Restriction '{restriction}' adds {len(RESTRICTED_INGREDIENTS[restriction])} forbidden ingredients")

    if not forbidden_ingredients:
        logger.debug("No forbidden ingredients found for specified restrictions")
        return recipes_df

    logger.debug(f"Total forbidden ingredients: {len(forbidden_ingredients)}")

    def has_forbidden_ingredient(ingredients_list) -> bool:
        """Vérifie si la recette contient un ingrédient interdit"""
        if not ingredients_list or not isinstance(ingredients_list, list):
            return False

        for ingredient in ingredients_list:
            if not ingredient:
                continue

            ing_lower = str(ingredient).lower().strip()

            # Vérifier si un ingrédient interdit est présent
            for forbidden in forbidden_ingredients:
                if forbidden in ing_lower:
                    logger.debug(f"Found forbidden ingredient '{forbidden}' in '{ingredient}'")
                    return True

        return False

    # Appliquer le filtre
    initial_count = len(recipes_df)
    recipes_df = recipes_df.copy()
    recipes_df['_has_forbidden'] = recipes_df['ingredients_list'].apply(has_forbidden_ingredient)
    filtered_df = recipes_df[~recipes_df['_has_forbidden']].drop(columns=['_has_forbidden'])

    filtered_count = len(filtered_df)
    removed_count = initial_count - filtered_count

    logger.info(f"Dietary restrictions filter: removed {removed_count} recipes ({initial_count} → {filtered_count})")

    return filtered_df


def filter_recipes_by_nutrition(recipes_df, max_calories=None, min_protein=None, max_carbs=None, max_fat=None):
    """
    Filtre les recettes selon les contraintes nutritionnelles

    Args:
        recipes_df: DataFrame de recettes
        max_calories: Calories maximum par recette (float, optionnel)
        min_protein: Protéines minimum en grammes (float, optionnel)
        max_carbs: Glucides maximum en grammes (float, optionnel)
        max_fat: Lipides maximum en grammes (float, optionnel)

    Returns:
        DataFrame filtré selon les critères nutritionnels
    """
    import pandas as pd

    # Si aucun filtre nutritionnel n'est spécifié, retourner tel quel
    if not any([max_calories, min_protein, max_carbs, max_fat]):
        logger.debug("No nutritional constraints to filter")
        return recipes_df

    filtered_df = recipes_df.copy()
    initial_count = len(filtered_df)

    logger.info(f"Filtering recipes by nutrition (calories≤{max_calories}, protein≥{min_protein}, carbs≤{max_carbs}, fat≤{max_fat})")

    # Filtrer par calories maximum
    if max_calories is not None:
        before = len(filtered_df)
        filtered_df = filtered_df[
            (filtered_df['calories'].isna()) |
            (filtered_df['calories'] <= max_calories)
        ]
        removed = before - len(filtered_df)
        if removed > 0:
            logger.debug(f"Max calories filter: removed {removed} recipes")

    # Filtrer par protéines minimum
    if min_protein is not None:
        before = len(filtered_df)
        filtered_df = filtered_df[
            (filtered_df['protein'].isna()) |
            (filtered_df['protein'] >= min_protein)
        ]
        removed = before - len(filtered_df)
        if removed > 0:
            logger.debug(f"Min protein filter: removed {removed} recipes")

    # Filtrer par glucides maximum
    if max_carbs is not None:
        before = len(filtered_df)
        filtered_df = filtered_df[
            (filtered_df['carbohydrates'].isna()) |
            (filtered_df['carbohydrates'] <= max_carbs)
        ]
        removed = before - len(filtered_df)
        if removed > 0:
            logger.debug(f"Max carbs filter: removed {removed} recipes")

    # Filtrer par lipides maximum
    if max_fat is not None:
        before = len(filtered_df)
        filtered_df = filtered_df[
            (filtered_df['total_fat'].isna()) |
            (filtered_df['total_fat'] <= max_fat)
        ]
        removed = before - len(filtered_df)
        if removed > 0:
            logger.debug(f"Max fat filter: removed {removed} recipes")

    filtered_count = len(filtered_df)
    removed_count = initial_count - filtered_count

    logger.info(f"Nutrition filter: removed {removed_count} recipes ({initial_count} → {filtered_count})")

    return filtered_df


def filter_recipes_by_disliked_ingredients(recipes_df, disliked_ingredients: List[str]):
    """
    Exclut les recettes contenant des ingrédients non désirés

    Args:
        recipes_df: DataFrame de recettes
        disliked_ingredients: List[str] - Liste d'ingrédients que l'utilisateur n'aime pas

    Returns:
        DataFrame filtré (sans les recettes contenant des ingrédients non désirés)
    """
    import pandas as pd

    if not disliked_ingredients or len(disliked_ingredients) == 0:
        logger.debug("No disliked ingredients to filter")
        return recipes_df

    # Normaliser les ingrédients non désirés
    disliked_normalized = [d.lower().strip() for d in disliked_ingredients]
    logger.info(f"Filtering recipes by disliked ingredients: {disliked_normalized}")

    def has_disliked_ingredient(ingredients_list) -> bool:
        """Vérifie si la recette contient un ingrédient non désiré"""
        if not ingredients_list or not isinstance(ingredients_list, list):
            return False

        for ingredient in ingredients_list:
            if not ingredient:
                continue

            ing_lower = str(ingredient).lower().strip()

            # Vérifier si un ingrédient non désiré est présent
            for disliked in disliked_normalized:
                if disliked in ing_lower:
                    logger.debug(f"Found disliked ingredient '{disliked}' in '{ingredient}'")
                    return True

        return False

    # Appliquer le filtre
    initial_count = len(recipes_df)
    recipes_df = recipes_df.copy()
    recipes_df['_has_disliked'] = recipes_df['ingredients_list'].apply(has_disliked_ingredient)
    filtered_df = recipes_df[~recipes_df['_has_disliked']].drop(columns=['_has_disliked'])

    filtered_count = len(filtered_df)
    removed_count = initial_count - filtered_count

    logger.info(f"Disliked ingredients filter: removed {removed_count} recipes ({initial_count} → {filtered_count})")

    return filtered_df


def apply_user_profile_filters(recipes_df, user_profile: Dict):
    """
    Applique tous les filtres du profil utilisateur aux recettes (fonction orchestratrice)

    Cette fonction coordonne l'application de tous les filtres basés sur le profil :
    - Allergies
    - Restrictions alimentaires (végétarien, végan, etc.)
    - Contraintes nutritionnelles (calories, protéines, etc.)
    - Ingrédients non désirés
    - Temps de préparation maximum

    Args:
        recipes_df: DataFrame de recettes
        user_profile: Dict contenant le profil utilisateur complet

    Returns:
        DataFrame filtré selon tous les critères du profil
    """
    import pandas as pd

    if not user_profile:
        logger.debug("No user profile provided, skipping profile filters")
        return recipes_df

    filtered_df = recipes_df.copy()
    initial_count = len(filtered_df)

    logger.info(f"=" * 80)
    logger.info(f"Applying user profile filters for user {user_profile.get('user_id', 'unknown')}")
    logger.info(f"Initial recipes count: {initial_count}")
    logger.info(f"=" * 80)

    # 1. Filtrer par allergies (PRIORITÉ HAUTE - sécurité)
    if user_profile.get('allergies'):
        logger.info(f"[1/5] Applying allergy filter: {user_profile['allergies']}")
        filtered_df = filter_recipes_by_allergies(filtered_df, user_profile['allergies'])
        logger.info(f"      → Remaining recipes: {len(filtered_df)}")
    else:
        logger.info(f"[1/5] No allergies specified, skipping")

    # 2. Filtrer par restrictions alimentaires (végétarien, végan, etc.)
    if user_profile.get('dietary_restrictions'):
        logger.info(f"[2/5] Applying dietary restrictions: {user_profile['dietary_restrictions']}")
        filtered_df = filter_recipes_by_dietary_restrictions(filtered_df, user_profile['dietary_restrictions'])
        logger.info(f"      → Remaining recipes: {len(filtered_df)}")
    else:
        logger.info(f"[2/5] No dietary restrictions specified, skipping")

    # 3. Filtrer par contraintes nutritionnelles
    nutritional_filters = {
        'max_calories': user_profile.get('max_calories'),
        'min_protein': user_profile.get('min_protein'),
        'max_carbs': user_profile.get('max_carbs'),
        'max_fat': user_profile.get('max_fat')
    }

    if any(nutritional_filters.values()):
        logger.info(f"[3/5] Applying nutritional constraints: {nutritional_filters}")
        filtered_df = filter_recipes_by_nutrition(
            filtered_df,
            max_calories=nutritional_filters['max_calories'],
            min_protein=nutritional_filters['min_protein'],
            max_carbs=nutritional_filters['max_carbs'],
            max_fat=nutritional_filters['max_fat']
        )
        logger.info(f"      → Remaining recipes: {len(filtered_df)}")
    else:
        logger.info(f"[3/5] No nutritional constraints specified, skipping")

    # 4. Filtrer par ingrédients non désirés
    if user_profile.get('disliked_ingredients'):
        logger.info(f"[4/5] Applying disliked ingredients filter: {user_profile['disliked_ingredients']}")
        filtered_df = filter_recipes_by_disliked_ingredients(filtered_df, user_profile['disliked_ingredients'])
        logger.info(f"      → Remaining recipes: {len(filtered_df)}")
    else:
        logger.info(f"[4/5] No disliked ingredients specified, skipping")

    # 5. Filtrer par temps de préparation maximum (du profil)
    if user_profile.get('max_prep_time'):
        logger.info(f"[5/5] Applying max prep time filter: {user_profile['max_prep_time']} minutes")
        before = len(filtered_df)
        filtered_df = filtered_df[
            (filtered_df['prep_time'].isna()) |
            (filtered_df['prep_time'] <= user_profile['max_prep_time'])
        ]
        removed = before - len(filtered_df)
        logger.info(f"      Max prep time filter: removed {removed} recipes")
        logger.info(f"      → Remaining recipes: {len(filtered_df)}")
    else:
        logger.info(f"[5/5] No max prep time specified, skipping")

    # Résumé final
    final_count = len(filtered_df)
    total_removed = initial_count - final_count
    percentage_kept = (final_count / initial_count * 100) if initial_count > 0 else 0

    logger.info(f"=" * 80)
    logger.info(f"Profile filtering complete:")
    logger.info(f"  - Initial recipes: {initial_count}")
    logger.info(f"  - Final recipes: {final_count}")
    logger.info(f"  - Removed: {total_removed} ({percentage_kept:.1f}% kept)")
    logger.info(f"=" * 80)

    return filtered_df


async def _get_fallback_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """
    Fallback recommendation method when model is not loaded.
    Utilise la base SQLite (tables Recipe & Review) au lieu des CSV.
    - Applique d'abord éventuellement le profil utilisateur (allergies, restrictions, nutrition, etc.)
    - Puis filtre par ingrédients et temps max
    - Score = match ingrédients + popularité (moyenne des ratings)
    """
    try:
        import pandas as pd
        import ast
        import math
        import numpy as np

        from .database import Recipe, Review

        # ------------------------------------------------------------------
        # 1) Charger les recettes depuis SQLite
        # ------------------------------------------------------------------
        db = get_db()
        session = db.get_session()

        recipes_query = (
            session
            .query(
                Recipe.recipe_id.label("recipe_id"),
                Recipe.ingredients_list.label("ingredients_list"),
                Recipe.minutes.label("prep_time"),      # alias minutes -> prep_time
                Recipe.name.label("Name"),
                Recipe.calories.label("calories"),
                Recipe.protein.label("protein"),
                Recipe.carbohydrates.label("carbohydrates"),
                Recipe.total_fat.label("total_fat"),
            )
        )

        recipes_df = pd.read_sql(recipes_query.statement, session.bind)

        # ------------------------------------------------------------------
        # 2) Charger les reviews pour calculer une popularité
        # ------------------------------------------------------------------
        recipe_scores = {}
        try:
            reviews_query = session.query(Review.recipe_id, Review.rating)
            reviews_df = pd.read_sql(reviews_query.statement, session.bind)
            if not reviews_df.empty:
                recipe_scores = reviews_df.groupby("recipe_id")["rating"].mean().to_dict()
        except Exception as e:
            logger.warning(f"Could not load reviews for popularity scores: {e}")
            recipe_scores = {}

        session.close()

        if recipes_df.empty:
            return RecommendationResponse(
                recipe_ids=[],
                scores=[],
                explanations=["Aucune recette trouvée dans la base."]
            )

        # ------------------------------------------------------------------
        # 3) Profil utilisateur (si demandé) : allergies, diet, nutrition, etc.
        # ------------------------------------------------------------------
        user_profile = None
        if getattr(request, "use_profile", True):
            try:
                from .main import db_instance
                if db_instance:
                    user_profile = db_instance.get_user_profile(request.user_id)
                    if user_profile:
                        logger.info(f"✅ Loaded profile for user {request.user_id}")
                        recipes_df = apply_user_profile_filters(recipes_df, user_profile)

                        if len(recipes_df) == 0:
                            logger.warning("⚠️  No recipes match user profile constraints after filtering")
                            logger.warning("   Relaxing filters to return some recommendations...")
                            # Re-load recipes without profile filters (too restrictive)
                            from .main import db_instance
                            if db_instance:
                                session = db_instance.get_session()
                                try:
                                    from .database import Recipe
                                    recipes_query = session.query(
                                        Recipe.recipe_id,
                                        Recipe.name,
                                        Recipe.minutes,
                                        Recipe.calories,
                                        Recipe.ingredients_list
                                    )
                                    recipes_df = pd.read_sql(recipes_query.statement, session.bind)
                                    logger.info(f"   Reloaded {len(recipes_df)} recipes without strict profile filters")
                                finally:
                                    session.close()
                            
                            # If still empty, return error
                            if recipes_df.empty:
                                return RecommendationResponse(
                                    recipe_ids=[],
                                    scores=[],
                                    explanations=[
                                        "Aucune recette trouvée. "
                                        "Essayez avec moins de filtres ou d'autres ingrédients."
                                    ],
                                )
                    else:
                        logger.info(f"No profile found for user {request.user_id}")
            except Exception as e:
                logger.warning(f"Could not load user profile: {e}")
        else:
            logger.info("Profile usage disabled by request (use_profile=False)")

        # ------------------------------------------------------------------
        # 4) Filtre par ingrédients disponibles (request.available_ingredients)
        # ------------------------------------------------------------------
        available_ings = set()
        if request.available_ingredients and len(request.available_ingredients) > 0:
            available_ings = {
                ing.lower().strip()
                for ing in request.available_ingredients
                if isinstance(ing, str) and ing.strip()
            }

            def calculate_ingredient_match(ingredients_val):
                """
                Calculate how well a recipe matches available ingredients
                Returns: (num_matched, total_recipe_ings, match_ratio, used_ingredients_count, missing_ings, matched_ings)
                """
                try:
                    # Rien / NaN -> pas d'ingrédients
                    if ingredients_val is None or (isinstance(ingredients_val, float) and math.isnan(ingredients_val)):
                        return (0, 0, 0.0, 0, [], [])

                    # Si c'est déjà une liste (JSON de la BDD)
                    if isinstance(ingredients_val, (list, tuple, set)):
                        ingredients = [str(x) for x in ingredients_val]

                    # Si c'est un array numpy
                    elif isinstance(ingredients_val, np.ndarray):
                        ingredients = [str(x) for x in ingredients_val.tolist()]

                    # Si c'est une string (représentation texte d'une liste)
                    elif isinstance(ingredients_val, str):
                        val = ingredients_val.strip()
                        if not val:
                            return (0, 0, 0.0, 0, [], [])
                        try:
                            parsed = ast.literal_eval(val)
                            if isinstance(parsed, (list, tuple, set)):
                                ingredients = [str(x) for x in parsed]
                            else:
                                ingredients = [s.strip() for s in val.split(",") if s.strip()]
                        except Exception:
                            ingredients = [s.strip() for s in val.split(",") if s.strip()]

                    else:
                        # Type inconnu -> on abandonne poliment
                        return (0, 0, 0.0, 0, [], [])

                    if len(ingredients) == 0:
                        return (0, 0, 0.0, 0, [], [])

                    # Normalisation des ingrédients de la recette
                    recipe_ings_normalized = {}
                    for ing in ingredients:
                        ing_normalized = str(ing).lower().strip()
                        if ing_normalized:
                            recipe_ings_normalized[ing_normalized] = str(ing)

                    recipe_ings_set = set(recipe_ings_normalized.keys())
                    matched_normalized = available_ings & recipe_ings_set
                    missing_normalized = recipe_ings_set - available_ings

                    num_matched = len(matched_normalized)
                    total_recipe = len(recipe_ings_set)
                    match_ratio = num_matched / total_recipe if total_recipe > 0 else 0.0

                    matched_list = [recipe_ings_normalized[ing] for ing in matched_normalized]
                    missing_list = [recipe_ings_normalized[ing] for ing in missing_normalized]

                    return (num_matched, total_recipe, match_ratio, num_matched, missing_list, matched_list)

                except Exception as e:
                    logger.warning(f"Error calculating ingredient match: {e}")
                    return (0, 0, 0.0, 0, [], [])

            match_data = recipes_df["ingredients_list"].apply(calculate_ingredient_match)
            recipes_df["ingredients_matched"] = match_data.apply(lambda x: x[0])
            recipes_df["recipe_total_ingredients"] = match_data.apply(lambda x: x[1])
            recipes_df["ingredient_match_ratio"] = match_data.apply(lambda x: x[2])
            recipes_df["ingredients_used_count"] = match_data.apply(lambda x: x[3])
            recipes_df["missing_ingredients"] = match_data.apply(lambda x: x[4])
            recipes_df["matched_ingredients"] = match_data.apply(lambda x: x[5])

            recipes_df["has_all_ingredients"] = (
                (recipes_df["ingredients_matched"] == recipes_df["recipe_total_ingredients"]) &
                (recipes_df["recipe_total_ingredients"] > 0) &
                (recipes_df["ingredients_matched"] > 0) &
                (recipes_df["missing_ingredients"].apply(lambda x: len(x) if isinstance(x, list) else 0) == 0)
            )

            # On garde seulement les recettes qui utilisent au moins 1 ingrédient
            # et avec un match ratio >= 0.2
            recipes_df = recipes_df[
                (recipes_df["ingredients_matched"] > 0) &
                (recipes_df["ingredient_match_ratio"] >= 0.2)
            ]
        else:
            recipes_df["ingredients_matched"] = 0
            recipes_df["recipe_total_ingredients"] = 0
            recipes_df["ingredient_match_ratio"] = 0.0
            recipes_df["ingredients_used_count"] = 0
            recipes_df["missing_ingredients"] = recipes_df.apply(lambda x: [], axis=1)
            recipes_df["matched_ingredients"] = recipes_df.apply(lambda x: [], axis=1)
            recipes_df["has_all_ingredients"] = False

        # ------------------------------------------------------------------
        # 5) Filtre max_time de la requête (en plus du max_prep_time du profil)
        # ------------------------------------------------------------------
        if request.max_time and "prep_time" in recipes_df.columns:
            recipes_df = recipes_df[recipes_df["prep_time"] <= request.max_time]

        # ------------------------------------------------------------------
        # 6) Score : popularité + match ingrédients
        # ------------------------------------------------------------------
        if len(recipes_df) > 0:
            recipes_df["raw_score"] = recipes_df["recipe_id"].map(lambda x: recipe_scores.get(x, 0.0))
            recipes_df["raw_score"] = recipes_df["raw_score"].fillna(0.0)

            max_popularity = recipes_df["raw_score"].max()
            if not pd.notna(max_popularity) or max_popularity <= 0:
                max_popularity = 5.0

            recipes_df["popularity_score"] = recipes_df["raw_score"] / max_popularity
            recipes_df["popularity_score"] = recipes_df["popularity_score"].fillna(0.0)

            if request.available_ingredients and len(request.available_ingredients) > 0:
                total_available = len(request.available_ingredients)

                recipes_df["ingredient_usage_ratio"] = (
                    recipes_df["ingredients_used_count"] / total_available
                    if total_available > 0 else 0
                )

                recipes_df["match_ratio_score"] = recipes_df["ingredient_match_ratio"]
                recipes_df["completeness_bonus"] = recipes_df["has_all_ingredients"].astype(float) * 0.20

                recipes_df["score"] = (
                    0.65 * recipes_df["ingredient_usage_ratio"] +
                    0.25 * recipes_df["match_ratio_score"] +
                    0.10 * recipes_df["popularity_score"] +
                    recipes_df["completeness_bonus"]
                )

                recipes_df["score"] = recipes_df["score"].clip(0, 1.0)
                recipes_df["score"] = recipes_df["score"].fillna(0.0)
            else:
                recipes_df["score"] = recipes_df["popularity_score"].fillna(0.0)
        else:
            recipes_df["score"] = 0.0

        # ------------------------------------------------------------------
        # 7) Tri + top_k + nettoyage des scores
        # ------------------------------------------------------------------
        recipes_df = recipes_df.sort_values("score", ascending=False, na_position="last")

        top_k = min(request.top_k, len(recipes_df))
        top_recipes = recipes_df.head(top_k)

        recipe_ids = top_recipes["recipe_id"].tolist()
        scores = top_recipes["score"].tolist()

        clean_scores = []
        for s in scores:
            try:
                f = float(s)
                if math.isnan(f) or math.isinf(f):
                    f = 0.0
            except Exception:
                f = 0.0
            clean_scores.append(f)
        scores = clean_scores

        # ------------------------------------------------------------------
        # 8) Explications
        # ------------------------------------------------------------------
        explanations = []
        for _, row in top_recipes.iterrows():
            name = row.get("Name", row.get("name", f"Recipe {row['recipe_id']}"))

            if "ingredients_used_count" in row and row["ingredients_used_count"] > 0:
                used = int(row["ingredients_used_count"])
                recipe_total = int(row["recipe_total_ingredients"]) if "recipe_total_ingredients" in row else 0
                match_pct = int(row["ingredient_match_ratio"] * 100) if "ingredient_match_ratio" in row else 0

                missing_ings = row.get("missing_ingredients", [])
                if not isinstance(missing_ings, list):
                    missing_ings = []
                missing_count = len(missing_ings)

                if missing_count != (recipe_total - used):
                    missing_count = recipe_total - used

                has_all = (
                    row.get("has_all_ingredients", False) and
                    missing_count == 0 and
                    used == recipe_total and
                    recipe_total > 0
                )

                if has_all:
                    explanations.append(
                        f"✅ Vous avez TOUS les ingrédients nécessaires ({used}/{recipe_total}) : {name}"
                    )
                elif missing_count > 0:
                    if len(missing_ings) > 0:
                        missing_display = ", ".join(missing_ings[:3])
                        if len(missing_ings) > 3:
                            missing_display += f" (+{len(missing_ings) - 3} autres)"
                        explanations.append(
                            f"⚠️ Il manque {missing_count} ingrédient(s) "
                            f"({used}/{recipe_total} disponibles) : {name}. "
                            f"Manquent : {missing_display}"
                        )
                    else:
                        explanations.append(
                            f"⚠️ Il manque {missing_count} ingrédient(s) "
                            f"({used}/{recipe_total} disponibles, {match_pct}%) : {name}"
                        )
                else:
                    explanations.append(
                        f"Utilise {used}/{recipe_total} ingrédients ({match_pct}% de la recette) : {name}"
                    )
            else:
                explanations.append(f"Recette populaire : {name}")

        return RecommendationResponse(
            recipe_ids=recipe_ids,
            scores=scores,
            explanations=explanations,
        )

    except Exception as e:
        logger.error(f"Error in fallback recommendations (DB): {e}", exc_info=True)
        return RecommendationResponse(
            recipe_ids=[],
            scores=[],
            explanations=[f"Error: {str(e)}"],
        )


@router.post("/log_interaction")
async def log_interaction(
    request: InteractionLogRequest
):
    """
    Log a user-recipe interaction
    
    Args:
        request: Interaction log request
        db: Database dependency
        
    Returns:
        Success message
    """
    try:
        db = get_db()
        db.log_interaction(
            user_id=request.user_id,
            recipe_id=request.recipe_id,
            interaction_type=request.interaction_type,
            rating=request.rating,
            review=request.review,
            available_ingredients=request.available_ingredients,
            session_id=request.session_id
        )
        
        return {"status": "success", "message": "Interaction logged"}
        
    except Exception as e:
        logger.error(f"Error logging interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/interactions")
async def get_user_interactions(
    user_id: int,
    limit: int = 100
):
    """
    Get user's interaction history
    
    Args:
        user_id: User ID
        limit: Maximum number of interactions
        db: Database dependency
        
    Returns:
        List of interactions
    """
    try:
        db = get_db()
        interactions = db.get_user_interactions(user_id, limit=limit)
        return {"user_id": user_id, "interactions": interactions}
        
    except Exception as e:
        logger.error(f"Error getting interactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recipe/{recipe_id}/reviews")
async def get_recipe_reviews(recipe_id: int, limit: int = 5):
    """
    Get reviews for a specific recipe
    
    Args:
        recipe_id: Recipe ID
        limit: Maximum number of reviews to return
        
    Returns:
        List of reviews with ratings and comments
    """
    try:
        import pandas as pd
        from pathlib import Path
        
        reviews_path = Path("data/raw/reviews.csv")
        if not reviews_path.exists():
            return {"reviews": []}
        
        # Load reviews for this recipe
        reviews_df = pd.read_csv(reviews_path, usecols=["RecipeId", "Rating", "Review", "AuthorName", "DateSubmitted"])
        recipe_reviews = reviews_df[reviews_df["RecipeId"] == recipe_id].copy()
        
        # Sort by date (most recent first) or rating (highest first)
        if "DateSubmitted" in recipe_reviews.columns:
            recipe_reviews = recipe_reviews.sort_values("DateSubmitted", ascending=False)
        elif "Rating" in recipe_reviews.columns:
            recipe_reviews = recipe_reviews.sort_values("Rating", ascending=False)
        
        # Get top reviews
        top_reviews = recipe_reviews.head(limit)
        
        # Format response
        reviews_list = []
        for _, row in top_reviews.iterrows():
            review_data = {
                "rating": float(row["Rating"]) if pd.notna(row["Rating"]) else None,
                "review": str(row["Review"]) if pd.notna(row["Review"]) else "",
                "author": str(row["AuthorName"]) if "AuthorName" in row and pd.notna(row["AuthorName"]) else "Anonymous",
                "date": str(row["DateSubmitted"]) if "DateSubmitted" in row and pd.notna(row["DateSubmitted"]) else None
            }
            reviews_list.append(review_data)
        
        return {"recipe_id": recipe_id, "reviews": reviews_list}
        
    except Exception as e:
        logger.error(f"Error getting reviews for recipe {recipe_id}: {e}")
        return {"recipe_id": recipe_id, "reviews": []}


# Database dependency will be created per request
def get_db():
    """Database dependency
        
    On réutilise l'instance globale créée dans main.py si elle existe,
    sinon on crée une instance SQLite par défaut.
    """
    try:
        from .main import db_instance
    except ImportError:
        db_instance = None

    if db_instance is None:
        # Fallback: API lancée "à cru" sans main.py
        return Database(database_type="sqlite", sqlite_path="data/saveeat.db")
    
    return db_instance



# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@router.post("/user/{user_id}/profile", response_model=UserProfileResponse)
async def create_or_update_profile(
    user_id: int,
    profile_data: UserProfileRequest
):
    """
    Create or update a user profile with preferences and dietary restrictions

    Args:
        user_id: User ID
        profile_data: Profile data to create/update

    Returns:
        Updated user profile
    """
    try:
        from .main import db_instance

        if db_instance is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        # Convert request to dict, excluding None values
        preferences = profile_data.model_dump(exclude_none=True)

        # Create or update profile
        profile = db_instance.create_user_profile(
            user_id=user_id,
            username=preferences.pop("username", None),
            email=preferences.pop("email", None),
            **preferences
        )

        return UserProfileResponse(**profile)

    except Exception as e:
        logger.error(f"Error creating/updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/profile", response_model=UserProfileResponse)
async def get_profile(user_id: int):
    """
    Get user profile by user ID

    Args:
        user_id: User ID

    Returns:
        User profile
    """
    try:
        from .main import db_instance

        if db_instance is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        profile = db_instance.get_user_profile(user_id)

        if profile is None:
            raise HTTPException(status_code=404, detail=f"Profile for user {user_id} not found")

        return UserProfileResponse(**profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/user/{user_id}/profile", response_model=UserProfileResponse)
async def update_profile_preferences(
    user_id: int,
    preferences: Dict[str, Any]
):
    """
    Update specific user preferences

    Args:
        user_id: User ID
        preferences: Dictionary of preferences to update

    Returns:
        Updated user profile
    """
    try:
        from .main import db_instance

        if db_instance is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        profile = db_instance.update_user_preferences(user_id, preferences)

        return UserProfileResponse(**profile)

    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user/{user_id}/profile")
async def delete_profile(user_id: int):
    """
    Delete user profile

    Args:
        user_id: User ID

    Returns:
        Success message
    """
    try:
        from .main import db_instance

        if db_instance is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        success = db_instance.delete_user_profile(user_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Profile for user {user_id} not found")

        return {"status": "success", "message": f"Profile for user {user_id} deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

