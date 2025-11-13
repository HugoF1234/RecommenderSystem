"""
Hybrid GNN Model for Save Eat
Combines graph neural networks with text embeddings for recipe recommendation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, SAGEConv, GATConv, HeteroConv
from torch_geometric.data import HeteroData
from typing import Dict, Optional
import logging

from .text_encoder import TextEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridGNN(nn.Module):
    """
    Hybrid GNN model combining graph structure with text features
    """
    
    def __init__(
        self,
        embedding_dim: int = 128,
        hidden_dim: int = 256,
        num_layers: int = 2,
        dropout: float = 0.3,
        activation: str = "relu",
        text_embedding_dim: int = 384,
        use_text_features: bool = True
    ):
        """
        Initialize hybrid GNN
        
        Args:
            embedding_dim: Base embedding dimension
            hidden_dim: Hidden layer dimension
            num_layers: Number of GNN layers
            dropout: Dropout rate
            activation: Activation function
            text_embedding_dim: Dimension of text embeddings
            use_text_features: Whether to use text features
        """
        super().__init__()
        
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout
        self.use_text_features = use_text_features
        
        # Activation function
        if activation == "relu":
            self.activation = F.relu
        elif activation == "gelu":
            self.activation = F.gelu
        else:
            self.activation = F.relu
        
        # Text encoder (optional)
        if use_text_features:
            self.text_encoder = TextEncoder(embedding_dim=text_embedding_dim)
            # Project text embeddings to embedding_dim
            self.text_projection = nn.Linear(text_embedding_dim, embedding_dim)
        else:
            self.text_encoder = None
            self.text_projection = None
        
        # User and recipe embeddings
        # These will be initialized from data
        self.user_embedding = None
        self.recipe_embedding = None
        
        # GNN layers for heterogeneous graph
        self.convs = nn.ModuleList()
        
        # First layer: input_dim -> hidden_dim
        if num_layers > 0:
            self.convs.append(
                HeteroConv({
                    ("user", "interacts_with", "recipe"): SAGEConv(embedding_dim, hidden_dim),
                    ("recipe", "contains", "ingredient"): SAGEConv(embedding_dim, hidden_dim),
                }, aggr="mean")
            )
            
            # Middle layers: hidden_dim -> hidden_dim
            for _ in range(num_layers - 1):
                self.convs.append(
                    HeteroConv({
                        ("user", "interacts_with", "recipe"): SAGEConv(hidden_dim, hidden_dim),
                        ("recipe", "contains", "ingredient"): SAGEConv(hidden_dim, hidden_dim),
                    }, aggr="mean")
                )
        
        # Final projection to embedding_dim
        if num_layers > 0:
            self.user_projection = nn.Linear(hidden_dim, embedding_dim)
            self.recipe_projection = nn.Linear(hidden_dim, embedding_dim)
        else:
            self.user_projection = nn.Identity()
            self.recipe_projection = nn.Identity()
        
        # Dropout layer
        self.dropout_layer = nn.Dropout(dropout)
    
    def initialize_embeddings(self, n_users: int, n_recipes: int, device: torch.device):
        """
        Initialize user and recipe embeddings
        
        Args:
            n_users: Number of users
            n_recipes: Number of recipes
            device: Device to place embeddings on
        """
        self.user_embedding = nn.Embedding(n_users, self.embedding_dim).to(device)
        self.recipe_embedding = nn.Embedding(n_recipes, self.embedding_dim).to(device)
        
        # Initialize with small random values
        nn.init.normal_(self.user_embedding.weight, std=0.1)
        nn.init.normal_(self.recipe_embedding.weight, std=0.1)
    
    def encode_text_features(self, recipe_texts: Dict[int, str], device: torch.device) -> torch.Tensor:
        """
        Encode text features for recipes
        
        Args:
            recipe_texts: Dictionary mapping recipe_idx to text
            device: Device
            
        Returns:
            Text embeddings tensor
        """
        if not self.use_text_features or self.text_encoder is None:
            return None
        
        # Get texts in order
        n_recipes = max(recipe_texts.keys()) + 1 if recipe_texts else 0
        texts = [recipe_texts.get(i, "") for i in range(n_recipes)]
        
        # Encode
        text_embeddings = self.text_encoder.encode_text(texts).to(device)
        
        # Project
        text_embeddings = self.text_projection(text_embeddings)
        
        return text_embeddings
    
    def forward(
        self,
        data: HeteroData,
        recipe_text_embeddings: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass
        
        Args:
            data: HeteroData graph
            recipe_text_embeddings: Optional pre-computed text embeddings
            
        Returns:
            Dictionary with user and recipe embeddings
        """
        # Get initial embeddings
        x_dict = {
            "user": self.user_embedding.weight,
            "recipe": self.recipe_embedding.weight
        }
        
        # Add text features to recipes if available
        if recipe_text_embeddings is not None:
            x_dict["recipe"] = x_dict["recipe"] + recipe_text_embeddings
        
        # Add ingredient embeddings if present
        if "ingredient" in data.x_dict:
            x_dict["ingredient"] = data.x_dict["ingredient"]
        
        # GNN layers
        for i, conv in enumerate(self.convs):
            x_dict = conv(x_dict, data.edge_index_dict)
            
            # Apply activation and dropout (except last layer)
            if i < len(self.convs) - 1:
                x_dict = {
                    k: self.dropout_layer(self.activation(v))
                    for k, v in x_dict.items()
                }
        
        # Final projections
        user_embeddings = self.user_projection(x_dict["user"])
        recipe_embeddings = self.recipe_projection(x_dict["recipe"])
        
        return {
            "user_embeddings": user_embeddings,
            "recipe_embeddings": recipe_embeddings
        }
    
    def predict(
        self,
        user_indices: torch.Tensor,
        recipe_indices: torch.Tensor,
        embeddings: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """
        Predict scores for user-recipe pairs
        
        Args:
            user_indices: User indices tensor
            recipe_indices: Recipe indices tensor
            embeddings: Dictionary with user and recipe embeddings
            
        Returns:
            Prediction scores tensor
        """
        user_emb = embeddings["user_embeddings"][user_indices]
        recipe_emb = embeddings["recipe_embeddings"][recipe_indices]
        
        # Dot product (can be extended to MLP)
        scores = (user_emb * recipe_emb).sum(dim=1)
        
        return scores

