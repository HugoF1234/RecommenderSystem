"""
Contextual Reranker for Save Eat
Re-ranks recommendations based on available ingredients, time constraints, and preferences
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Optional, Tuple
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextualReranker(nn.Module):
    """
    Re-ranks recommendations using contextual features
    """
    
    def __init__(
        self,
        input_dim: int = 128,
        hidden_dims: List[int] = [256, 128, 64],
        dropout: float = 0.2,
        context_dim: int = 50  # Max ingredients + time + preferences
    ):
        """
        Initialize reranker
        
        Args:
            input_dim: Dimension of base recommendation scores
            hidden_dims: List of hidden layer dimensions
            dropout: Dropout rate
            context_dim: Dimension of contextual features
        """
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.dropout = dropout
        self.context_dim = context_dim
        
        # Build MLP
        layers = []
        input_size = input_dim + context_dim
        
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(input_size, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            input_size = hidden_dim
        
        # Output layer (single score)
        layers.append(nn.Linear(input_size, 1))
        
        self.mlp = nn.Sequential(*layers)
    
    def encode_context(
        self,
        available_ingredients: List[str],
        recipe_ingredients: List[str],
        prep_time: float,
        max_time: Optional[float] = None,
        dietary_preferences: Optional[List[str]] = None
    ) -> torch.Tensor:
        """
        Encode contextual features
        
        Args:
            available_ingredients: List of available ingredients
            recipe_ingredients: List of recipe ingredients
            prep_time: Recipe preparation time
            max_time: Maximum available time (optional)
            dietary_preferences: List of dietary preferences (optional)
            
        Returns:
            Context feature vector
        """
        features = []
        
        # Ingredient overlap (normalized)
        available_set = set(str(ing).lower().strip() for ing in available_ingredients)
        recipe_set = set(str(ing).lower().strip() for ing in recipe_ingredients)
        
        overlap = len(available_set & recipe_set)
        coverage = overlap / len(recipe_set) if recipe_set else 0.0
        missing = len(recipe_set - available_set) / max(len(recipe_set), 1)
        
        features.extend([coverage, missing, overlap / max(len(available_set), 1)])
        
        # Time constraints
        if max_time is not None:
            time_ratio = prep_time / max_time if max_time > 0 else 1.0
            time_feasible = 1.0 if prep_time <= max_time else 0.0
            features.extend([time_ratio, time_feasible, prep_time / 60.0])  # Normalize to hours
        else:
            features.extend([0.0, 1.0, prep_time / 60.0])
        
        # Dietary preferences (binary features)
        # This is simplified - can be extended based on recipe metadata
        if dietary_preferences:
            # Placeholder - would check recipe metadata
            features.extend([1.0] * len(dietary_preferences))
        else:
            features.extend([0.0] * 4)  # Placeholder for common preferences
        
        # Pad or truncate to context_dim
        while len(features) < self.context_dim:
            features.append(0.0)
        features = features[:self.context_dim]
        
        return torch.tensor(features, dtype=torch.float32)
    
    def forward(
        self,
        base_scores: torch.Tensor,
        context_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            base_scores: Base recommendation scores (batch_size,)
            context_features: Context features (batch_size, context_dim)
            
        Returns:
            Re-ranked scores (batch_size,)
        """
        # Concatenate scores and context
        combined = torch.cat([
            base_scores.unsqueeze(1),
            context_features
        ], dim=1)
        
        # MLP
        reranked_scores = self.mlp(combined).squeeze(1)
        
        return reranked_scores
    
    def rerank(
        self,
        base_scores: torch.Tensor,
        context_features: torch.Tensor,
        top_k: int = 20
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Re-rank and return top-k
        
        Args:
            base_scores: Base recommendation scores
            context_features: Context features
            top_k: Number of top items to return
            
        Returns:
            Re-ranked scores and indices
        """
        reranked_scores = self.forward(base_scores, context_features)
        
        # Get top-k
        top_scores, top_indices = torch.topk(reranked_scores, min(top_k, len(reranked_scores)))
        
        return top_scores, top_indices

