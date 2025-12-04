"""
Graph Builder for Save Eat
Constructs bipartite graphs for GNN-based recommendation
"""

import torch
from torch_geometric.data import HeteroData
from torch_geometric.transforms import ToUndirected
import pandas as pd
from typing import Dict, List, Tuple, Optional
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Builds heterogeneous graphs for recipe recommendation
    Creates graphs with user, recipe, and ingredient nodes
    """
    
    def __init__(self, embedding_dim: int = 128):
        """
        Initialize graph builder
        
        Args:
            embedding_dim: Dimension for node embeddings
        """
        self.embedding_dim = embedding_dim
    
    def build_user_recipe_graph(
        self,
        interactions: pd.DataFrame,
        mappings: Dict,
        edge_attr: Optional[str] = "rating"
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Build user-recipe bipartite graph
        
        Args:
            interactions: Interactions DataFrame with user_idx and recipe_idx
            mappings: ID mappings dictionary
            edge_attr: Column name for edge attributes (rating)
            
        Returns:
            Edge indices and edge attributes tensors
        """
        user_indices = interactions["user_idx"].values
        recipe_indices = interactions["recipe_idx"].values
        
        # Offset recipe indices to avoid collisions with user indices
        n_users = len(mappings["user_to_idx"])
        recipe_indices_offset = recipe_indices + n_users
        
        # Create edge indices: [source, target]
        # Users -> Recipes
        # Use int64 to handle large IDs
        edge_index = torch.tensor([
            user_indices.astype(np.int64).tolist(),
            recipe_indices_offset.astype(np.int64).tolist()
        ], dtype=torch.int64)
        
        # Edge attributes (ratings)
        if edge_attr and edge_attr in interactions.columns:
            edge_attr_values = interactions[edge_attr].fillna(3.0).values
            edge_attr_tensor = torch.tensor(edge_attr_values, dtype=torch.float)
        else:
            edge_attr_tensor = torch.ones(len(interactions), dtype=torch.float)
        
        return edge_index, edge_attr_tensor
    
    def build_recipe_ingredient_graph(
        self,
        recipes: pd.DataFrame,
        mappings: Dict
    ) -> Tuple[torch.Tensor, Dict[str, int]]:
        """
        Build recipe-ingredient bipartite graph
        
        Args:
            recipes: Recipes DataFrame with ingredients_list
            mappings: ID mappings dictionary
            
        Returns:
            Edge indices and ingredient_to_idx mapping
        """
        # Collect all unique ingredients
        all_ingredients = set()
        for ingredients_list in recipes["ingredients_list"]:
            if isinstance(ingredients_list, list):
                all_ingredients.update(str(ing).lower().strip() for ing in ingredients_list)
        
        ingredient_to_idx = {ing: idx for idx, ing in enumerate(sorted(all_ingredients))}
        n_ingredients = len(ingredient_to_idx)
        
        # Build edges
        recipe_indices = []
        ingredient_indices = []
        
        n_users = len(mappings["user_to_idx"])
        n_recipes = len(mappings["recipe_to_idx"])
        
        # Recipe indices offset (after users)
        recipe_offset = n_users
        # Ingredient indices offset (after users + recipes)
        ingredient_offset = n_users + n_recipes
        
        for _, row in recipes.iterrows():
            recipe_idx = row["recipe_idx"]
            ingredients_list = row["ingredients_list"]
            
            if isinstance(ingredients_list, list):
                for ing in ingredients_list:
                    ing_normalized = str(ing).lower().strip()
                    if ing_normalized in ingredient_to_idx:
                        ing_idx = ingredient_to_idx[ing_normalized]
                        recipe_indices.append(recipe_idx + recipe_offset)
                        ingredient_indices.append(ing_idx + ingredient_offset)
        
        if recipe_indices:
            edge_index = torch.tensor([
                recipe_indices,
                ingredient_indices
            ], dtype=torch.int64)
        else:
            edge_index = torch.empty((2, 0), dtype=torch.int64)
        
        logger.info(f"Built recipe-ingredient graph: {len(recipe_indices)} edges, {n_ingredients} ingredients")
        
        return edge_index, ingredient_to_idx
    
    def build_hetero_graph(
        self,
        interactions: pd.DataFrame,
        recipes: pd.DataFrame,
        mappings: Dict,
        include_ingredients: bool = True
    ) -> HeteroData:
        """
        Build complete heterogeneous graph
        
        Args:
            interactions: Interactions DataFrame
            recipes: Recipes DataFrame with ingredients
            mappings: ID mappings dictionary
            include_ingredients: Whether to include ingredient nodes
            
        Returns:
            HeteroData graph object
        """
        data = HeteroData()
        
        n_users = len(mappings["user_to_idx"])
        n_recipes = len(mappings["recipe_to_idx"])
        
        # Initialize node features (will be learned)
        data["user"].x = torch.randn(n_users, self.embedding_dim)
        data["recipe"].x = torch.randn(n_recipes, self.embedding_dim)
        
        # Build user-recipe edges
        user_recipe_edge_index, user_recipe_edge_attr = self.build_user_recipe_graph(
            interactions, mappings
        )
        data["user", "interacts_with", "recipe"].edge_index = user_recipe_edge_index
        data["user", "interacts_with", "recipe"].edge_attr = user_recipe_edge_attr
        
        # Build recipe-ingredient edges
        if include_ingredients:
            recipe_ingredient_edge_index, ingredient_to_idx = self.build_recipe_ingredient_graph(
                recipes, mappings
            )
            
            n_ingredients = len(ingredient_to_idx)
            data["ingredient"].x = torch.randn(n_ingredients, self.embedding_dim)
            
            # Adjust recipe indices in ingredient edges (already offset in function)
            data["recipe", "contains", "ingredient"].edge_index = recipe_ingredient_edge_index
            
            # Store ingredient mapping
            data.ingredient_to_idx = ingredient_to_idx
        
        # Store mappings
        data.mappings = mappings
        data.n_users = n_users
        data.n_recipes = n_recipes
        
        logger.info(f"Built heterogeneous graph: {n_users} users, {n_recipes} recipes")
        if include_ingredients:
            logger.info(f"  + {n_ingredients} ingredients")
        
        return data

