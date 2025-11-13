"""
Text Encoder for Save Eat
Encodes recipe text (titles, descriptions, steps) using transformers
"""

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextEncoder(nn.Module):
    """
    Encodes text features using pre-trained transformers
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        embedding_dim: int = 384,
        max_length: int = 512
    ):
        """
        Initialize text encoder
        
        Args:
            model_name: HuggingFace model name
            embedding_dim: Output embedding dimension
            max_length: Maximum sequence length
        """
        super().__init__()
        
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.max_length = max_length
        
        # Load tokenizer and model
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            logger.info(f"Loaded model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
        
        # Projection layer to match embedding_dim if needed
        model_dim = self.model.config.hidden_size
        if model_dim != embedding_dim:
            self.projection = nn.Linear(model_dim, embedding_dim)
        else:
            self.projection = nn.Identity()
        
        # Freeze base model (optional - can be trained)
        # self.model.requires_grad_(False)
    
    def encode_text(self, texts: List[str]) -> torch.Tensor:
        """
        Encode a list of text strings
        
        Args:
            texts: List of text strings
            
        Returns:
            Tensor of shape (batch_size, embedding_dim)
        """
        if not texts:
            return torch.zeros((0, self.embedding_dim))
        
        # Tokenize
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        # Move to device
        device = next(self.parameters()).device
        encoded = {k: v.to(device) for k, v in encoded.items()}
        
        # Get embeddings
        with torch.no_grad() if not self.training else torch.enable_grad():
            outputs = self.model(**encoded)
            
            # Use mean pooling of last hidden state
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
            # Project to target dimension
            embeddings = self.projection(embeddings)
        
        return embeddings
    
    def forward(self, texts: List[str]) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            texts: List of text strings
            
        Returns:
            Text embeddings tensor
        """
        return self.encode_text(texts)

