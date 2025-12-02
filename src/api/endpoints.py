"""
API Endpoints for Save Eat
FastAPI endpoints for recommendations and logging
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
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


# Global model and data (will be initialized at startup)
model = None
graph_data = None
recipe_data = None
reranker = None
mappings = None


def initialize_model(model_path: str, graph_data_path: str, recipe_data_path: str, mappings_path: str):
    """Initialize model and data (called at startup)"""
    global model, graph_data, recipe_data, reranker, mappings
    
    # Load model, graph_data, recipe_data, mappings
    # This is a placeholder - actual implementation depends on how data is stored
    logger.info("Initializing model...")
    # model = HybridGNN(...)
    # model.load_state_dict(torch.load(model_path))
    # etc.
    
    logger.info("Model initialized")


@router.get("/recipe/{recipe_id}")
async def get_recipe(recipe_id: int):
    """
    Get recipe details by ID
    
    Args:
        recipe_id: Recipe ID
        
    Returns:
        Recipe details
    """
    try:
        import pandas as pd
        import ast
        from pathlib import Path
        
        recipes_path = Path("data/processed/recipes.csv")
        if not recipes_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Load recipe from processed CSV first
        recipes_df = pd.read_csv(recipes_path)
        recipe = recipes_df[recipes_df["recipe_id"] == recipe_id]
        
        if recipe.empty:
            raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")
        
        recipe = recipe.iloc[0]
        
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
    Get list of available ingredients
    
    Args:
        limit: Maximum number of ingredients to return
        
    Returns:
        List of ingredients
    """
    try:
        import pandas as pd
        import ast
        from pathlib import Path
        
        recipes_path = Path("data/processed/recipes.csv")
        if not recipes_path.exists():
            logger.warning(f"Recipes file not found at {recipes_path.absolute()}, returning default ingredients")
            # Return a basic list of common ingredients for demo purposes
            default_ingredients = [
                "tomato", "onion", "garlic", "olive oil", "salt", "pepper", "chicken",
                "beef", "pork", "fish", "rice", "pasta", "potato", "carrot", "celery",
                "bell pepper", "mushroom", "cheese", "milk", "butter", "flour", "egg",
                "lemon", "lime", "herbs", "spices", "bread", "lettuce", "cucumber"
            ]
            return {"ingredients": default_ingredients}
        
        # Load recipes and extract ingredients - load more to get better coverage
        df = pd.read_csv(recipes_path, usecols=["ingredients_list"], nrows=None)  # Load all
        all_ingredients = set()
        ingredient_counts = {}  # Count occurrences for better sorting
        
        for row in df["ingredients_list"]:
            try:
                if pd.notna(row):
                    ingredients = ast.literal_eval(str(row)) if isinstance(row, str) else row
                    if isinstance(ingredients, list):
                        for ing in ingredients:
                            ing_clean = str(ing).strip().lower()
                            if ing_clean and len(ing_clean) > 1:  # Filter out single characters
                                all_ingredients.add(ing_clean)
                                ingredient_counts[ing_clean] = ingredient_counts.get(ing_clean, 0) + 1
            except Exception as e:
                continue
        
        # Sort by frequency (most common first) then alphabetically
        sorted_ingredients = sorted(
            list(all_ingredients),
            key=lambda x: (-ingredient_counts.get(x, 0), x)  # Negative for descending count
        )[:limit]
        
        if not sorted_ingredients:
            logger.warning("No ingredients found in recipes file, returning default ingredients")
            default_ingredients = [
                "tomato", "onion", "garlic", "olive oil", "salt", "pepper", "chicken",
                "beef", "pork", "fish", "rice", "pasta", "potato", "carrot", "celery"
            ]
            return {"ingredients": default_ingredients}
        
        return {"ingredients": sorted_ingredients}
        
    except Exception as e:
        logger.error(f"Error getting ingredients: {e}", exc_info=True)
        # Return default ingredients on error
        default_ingredients = [
            "tomato", "onion", "garlic", "olive oil", "salt", "pepper", "chicken",
            "beef", "pork", "fish", "rice", "pasta", "potato", "carrot", "celery"
        ]
        return {"ingredients": default_ingredients}


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
            # Cold start: return popular recipes
            return RecommendationResponse(
                recipe_ids=[],
                scores=[],
                explanations=["New user: Please rate some recipes first"]
            )
        
        # Get base recommendations from GNN
        model.eval()
        with torch.no_grad():
            embeddings = model(graph_data)
            
            user_emb = embeddings["user_embeddings"][user_idx]
            recipe_embs = embeddings["recipe_embeddings"]
            
            # Compute scores
            scores = torch.matmul(user_emb.unsqueeze(0), recipe_embs.T).squeeze().cpu().numpy()
        
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
                    
                    recipe_ingredients = recipe.get("ingredients_list", [])
                    prep_time = recipe.get("prep_time", 30)
                    
                    context = reranker.encode_context(
                        available_ingredients=request.available_ingredients or [],
                        recipe_ingredients=recipe_ingredients,
                        prep_time=prep_time,
                        max_time=request.max_time,
                        dietary_preferences=request.dietary_preferences
                    )
                    context_features.append(context)
                    reranked_scores.append(scores[recipe_idx])
                
                if context_features:
                    context_tensor = torch.stack(context_features)
                    scores_tensor = torch.tensor(reranked_scores)
                    
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
        
        # Generate explanations (simplified)
        explanations = []
        for recipe_id in recipe_ids:
            recipe = recipe_data[recipe_data["recipe_id"] == recipe_id].iloc[0]
            name = recipe.get("name", f"Recipe {recipe_id}")
            explanations.append(f"Recommended: {name}")
        
        return RecommendationResponse(
            recipe_ids=recipe_ids,
            scores=final_scores,
            explanations=explanations
        )
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_fallback_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """
    Fallback recommendation method when model is not loaded
    Returns popular recipes filtered by available ingredients
    """
    try:
        import pandas as pd
        import ast
        from pathlib import Path
        
        recipes_path = Path("data/processed/recipes.csv")
        interactions_path = Path("data/processed/train.csv")
        
        if not recipes_path.exists():
            return RecommendationResponse(
                recipe_ids=[],
                scores=[],
                explanations=["Dataset not found. Please run preprocessing first."]
            )
        
        # Load recipes
        recipes_df = pd.read_csv(recipes_path)
        
        # Load interactions to get popularity scores
        recipe_scores = {}
        if interactions_path.exists():
            interactions_df = pd.read_csv(interactions_path, usecols=["recipe_id", "rating"], nrows=100000)
            recipe_scores = interactions_df.groupby("recipe_id")["rating"].mean().to_dict()
        
        # Process available ingredients if provided
        available_ings = set()
        if request.available_ingredients and len(request.available_ingredients) > 0:
            available_ings = set(ing.lower().strip() for ing in request.available_ingredients)
            
            # Calculate ingredient match scores for each recipe
            def calculate_ingredient_match(ingredients_str):
                """
                Calculate how well a recipe matches available ingredients
                Returns: (num_matched, total_recipe_ings, match_ratio, used_ingredients_count, missing_ings, matched_ings)
                """
                try:
                    if pd.isna(ingredients_str):
                        return (0, 0, 0.0, 0, [], [])
                    ingredients = ast.literal_eval(str(ingredients_str)) if isinstance(ingredients_str, str) else ingredients_str
                    if isinstance(ingredients, list) and len(ingredients) > 0:
                        # Create normalized mappings for both recipe and available ingredients
                        recipe_ings_normalized = {}  # normalized -> original
                        for ing in ingredients:
                            ing_normalized = str(ing).lower().strip()
                            recipe_ings_normalized[ing_normalized] = str(ing)
                        
                        recipe_ings_set = set(recipe_ings_normalized.keys())
                        matched_normalized = available_ings & recipe_ings_set
                        missing_normalized = recipe_ings_set - available_ings  # Ingrédients nécessaires mais non disponibles
                        
                        num_matched = len(matched_normalized)
                        total_recipe = len(recipe_ings_set)
                        match_ratio = num_matched / total_recipe if total_recipe > 0 else 0.0
                        
                        # Convert to lists of original ingredient names
                        matched_list = [recipe_ings_normalized[ing] for ing in matched_normalized]
                        missing_list = [recipe_ings_normalized[ing] for ing in missing_normalized]
                        
                        return (num_matched, total_recipe, match_ratio, num_matched, missing_list, matched_list)
                    return (0, 0, 0.0, 0, [], [])
                except Exception as e:
                    logger.warning(f"Error calculating ingredient match: {e}")
                    return (0, 0, 0.0, 0, [], [])
            
            # Calculate match metrics for all recipes
            match_data = recipes_df["ingredients_list"].apply(calculate_ingredient_match)
            recipes_df["ingredients_matched"] = match_data.apply(lambda x: x[0])
            recipes_df["recipe_total_ingredients"] = match_data.apply(lambda x: x[1])
            recipes_df["ingredient_match_ratio"] = match_data.apply(lambda x: x[2])
            recipes_df["ingredients_used_count"] = match_data.apply(lambda x: x[3])
            recipes_df["missing_ingredients"] = match_data.apply(lambda x: x[4])  # List of missing ingredients
            recipes_df["matched_ingredients"] = match_data.apply(lambda x: x[5])  # List of matched ingredients
            
            # Check if recipe has ALL ingredients (100% match) - STRICT check
            # Must have: matched == total AND total > 0 AND no missing ingredients
            recipes_df["has_all_ingredients"] = (
                (recipes_df["ingredients_matched"] == recipes_df["recipe_total_ingredients"]) &
                (recipes_df["recipe_total_ingredients"] > 0) &
                (recipes_df["ingredients_matched"] > 0) &
                (recipes_df["missing_ingredients"].apply(lambda x: len(x) if isinstance(x, list) else 0) == 0)
            )
            
            # Filter: recipe must use at least 1 ingredient from available list
            # LOWER the threshold to 20% to allow more recipes (don't require high match)
            # The scoring system will prioritize recipes with more ingredients in common
            recipes_df = recipes_df[
                (recipes_df["ingredients_matched"] > 0) & 
                (recipes_df["ingredient_match_ratio"] >= 0.2)  # Lowered from 0.3 to allow more variety
            ]
        else:
            # No ingredient filtering - all recipes eligible
            recipes_df["ingredients_matched"] = 0
            recipes_df["recipe_total_ingredients"] = 0
            recipes_df["ingredient_match_ratio"] = 0.0
            recipes_df["ingredients_used_count"] = 0
            recipes_df["missing_ingredients"] = recipes_df.apply(lambda x: [], axis=1)
            recipes_df["matched_ingredients"] = recipes_df.apply(lambda x: [], axis=1)
            recipes_df["has_all_ingredients"] = False
        
        # Filter by max_time if provided
        if request.max_time and "prep_time" in recipes_df.columns:
            recipes_df = recipes_df[recipes_df["prep_time"] <= request.max_time]
        
        # Sort by ingredient usage first (recipes using most ingredients from selection)
        # Then by popularity/rating
        if len(recipes_df) > 0:
            # Normalize popularity score
            recipes_df["raw_score"] = recipes_df["recipe_id"].map(lambda x: recipe_scores.get(x, 0))
            max_popularity = recipes_df["raw_score"].max() if recipes_df["raw_score"].max() > 0 else 5.0
            recipes_df["popularity_score"] = recipes_df["raw_score"] / max_popularity
            
            # Calculate final score: prioritize recipes with most ingredients in common
            # Score should reflect REAL match quality, prioritizing recipes using MOST of your ingredients
            if request.available_ingredients and len(request.available_ingredients) > 0:
                total_available = len(request.available_ingredients)
                
                # Score is based on: how many of YOUR ingredients are used (primary)
                # and what percentage of the RECIPE ingredients you have (secondary)
                
                # Primary: Number of ingredients used (normalize to 0-1 relative to YOUR ingredients)
                # A recipe using 5/7 of your ingredients gets higher score than one using 1/7
                recipes_df["ingredient_usage_ratio"] = recipes_df["ingredients_used_count"] / total_available if total_available > 0 else 0
                
                # Secondary: Match ratio (percentage of recipe ingredients you have)
                recipes_df["match_ratio_score"] = recipes_df["ingredient_match_ratio"]
                
                # Small bonus if recipe has ALL ingredients (allows reaching higher scores)
                recipes_df["completeness_bonus"] = recipes_df["has_all_ingredients"].astype(float) * 0.20
                
                # Combined score:
                # - 65% weight on ingredient usage (recipes using MORE of your ingredients rank higher)
                # - 25% weight on match ratio (recipes where you have high % of needed ingredients)
                # - 10% weight on popularity
                # - 20% bonus if you have ALL ingredients (max possible score = 1.20, capped to 1.0)
                recipes_df["score"] = (
                    0.65 * recipes_df["ingredient_usage_ratio"] +
                    0.25 * recipes_df["match_ratio_score"] +
                    0.10 * recipes_df["popularity_score"] +
                    recipes_df["completeness_bonus"]
                )
                
                # Cap at 1.0 for display
                recipes_df["score"] = recipes_df["score"].clip(0, 1.0)
            else:
                # No ingredients selected - sort by popularity only
                recipes_df["score"] = recipes_df["popularity_score"]
        else:
            recipes_df["score"] = 0.0
        
        # Sort by score (descending) - recipes using most ingredients first
        recipes_df = recipes_df.sort_values("score", ascending=False, na_position="last")
        
        # Get top-k
        top_k = min(request.top_k, len(recipes_df))
        top_recipes = recipes_df.head(top_k)
        
        recipe_ids = top_recipes["recipe_id"].tolist()
        scores = top_recipes["score"].tolist()
        
        # Generate explanations with ingredient match info
        explanations = []
        for _, row in top_recipes.iterrows():
            name = row.get("Name", row.get("name", f"Recipe {row['recipe_id']}"))
            
            # Add ingredient match information if available
            if "ingredients_used_count" in row and row["ingredients_used_count"] > 0:
                used = int(row["ingredients_used_count"])
                recipe_total = int(row["recipe_total_ingredients"]) if "recipe_total_ingredients" in row else 0
                match_pct = int(row["ingredient_match_ratio"] * 100) if "ingredient_match_ratio" in row else 0
                
                # Get missing ingredients list
                missing_ings = row.get("missing_ingredients", [])
                if not isinstance(missing_ings, list):
                    missing_ings = []
                missing_count = len(missing_ings)
                
                # Double-check: if missing_count doesn't match, recalculate
                if missing_count != (recipe_total - used):
                    missing_count = recipe_total - used
                
                # STRICT check: recipe has ALL ingredients only if:
                # 1. has_all_ingredients flag is True
                # 2. missing_count is 0
                # 3. used == recipe_total
                has_all = (
                    row.get("has_all_ingredients", False) and 
                    missing_count == 0 and 
                    used == recipe_total and 
                    recipe_total > 0
                )
                
                if has_all:
                    explanations.append(f"✅ Vous avez TOUS les ingrédients nécessaires ({used}/{recipe_total}): {name}")
                elif missing_count > 0:
                    # Show missing ingredients information
                    if len(missing_ings) > 0:
                        # Show first 2-3 missing ingredients
                        missing_display = ", ".join(missing_ings[:3])
                        if len(missing_ings) > 3:
                            missing_display += f" (+{len(missing_ings) - 3} autres)"
                        explanations.append(f"⚠️ Il manque {missing_count} ingrédient(s) ({used}/{recipe_total} disponibles): {name}. Manquent: {missing_display}")
                    else:
                        explanations.append(f"⚠️ Il manque {missing_count} ingrédient(s) ({used}/{recipe_total} disponibles, {match_pct}%): {name}")
                else:
                    explanations.append(f"Utilise {used}/{recipe_total} ingrédients ({match_pct}% de la recette): {name}")
            else:
                explanations.append(f"Recette populaire: {name}")
        
        return RecommendationResponse(
            recipe_ids=recipe_ids,
            scores=scores,
            explanations=explanations
        )
        
    except Exception as e:
        logger.error(f"Error in fallback recommendations: {e}")
        return RecommendationResponse(
            recipe_ids=[],
            scores=[],
            explanations=[f"Error: {str(e)}"]
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
    """Database dependency"""
    # Will be initialized from config in main.py
    # For now, create a simple instance
    db = Database(database_type="sqlite", sqlite_path="data/saveeat.db")
    return db

