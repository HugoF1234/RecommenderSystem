"""
Training Module for Save Eat
Handles model training loop and checkpointing
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
from tqdm import tqdm

from ..models.gnn_model import HybridGNN
from .evaluation import Evaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InteractionDataset(Dataset):
    """
    Dataset for user-recipe interactions
    """
    
    def __init__(self, interactions: Dict, n_negatives: int = 5):
        """
        Initialize dataset
        
        Args:
            interactions: Interactions DataFrame
            n_negatives: Number of negative samples per positive
        """
        self.interactions = interactions
        self.users = interactions["user_idx"].values
        self.recipes = interactions["recipe_idx"].values
        self.ratings = interactions.get("rating", np.ones(len(interactions))).values
        
        # Get unique recipes for negative sampling
        self.all_recipes = interactions["recipe_idx"].unique()
        self.user_recipes = interactions.groupby("user_idx")["recipe_idx"].apply(set).to_dict()
        
        self.n_negatives = n_negatives
    
    def __len__(self):
        return len(self.interactions) * (1 + self.n_negatives)
    
    def __getitem__(self, idx):
        # Get positive interaction
        pos_idx = idx // (1 + self.n_negatives)
        user = self.users[pos_idx]
        recipe = self.recipes[pos_idx]
        rating = self.ratings[pos_idx]
        
        # Sample negative if needed
        if idx % (1 + self.n_negatives) == 0:
            # Positive sample
            label = 1.0
            recipe = recipe
        else:
            # Negative sample
            label = 0.0
            # Sample negative recipe not interacted by user
            user_positive = self.user_recipes.get(user, set())
            negative_candidates = list(set(self.all_recipes) - user_positive)
            if negative_candidates:
                recipe = np.random.choice(negative_candidates)
            else:
                recipe = np.random.choice(self.all_recipes)
        
        return {
            "user_idx": user,
            "recipe_idx": recipe,
            "label": label,
            "rating": rating
        }


class Trainer:
    """
    Trainer for HybridGNN model
    """
    
    def __init__(
        self,
        model: HybridGNN,
        train_data: Dict,
        val_data: Dict,
        config: Dict,
        device: torch.device
    ):
        """
        Initialize trainer
        
        Args:
            model: HybridGNN model
            train_data: Training data dictionary
            val_data: Validation data dictionary
            config: Training configuration
            device: Device
        """
        self.model = model.to(device)
        self.train_data = train_data
        self.val_data = val_data
        self.config = config
        self.device = device
        
        # Optimizer with better settings for GNN training
        self.optimizer = optim.AdamW(
            model.parameters(),
            lr=config.get("learning_rate", 0.001),
            weight_decay=config.get("weight_decay", 0.0001),
            betas=(0.9, 0.999)
        )
        
        # Learning rate scheduler for better convergence
        if config.get("use_learning_rate_scheduler", False):
            self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer,
                mode='min',
                factor=config.get("scheduler_factor", 0.5),
                patience=config.get("scheduler_patience", 3),
                verbose=True
            )
        else:
            self.scheduler = None
        
        # Loss function (BCE with logits) - can be extended to BPR loss for ranking
        self.criterion = nn.BCEWithLogitsLoss()
        
        # Dataset and dataloader
        train_dataset = InteractionDataset(
            train_data["train"],
            n_negatives=config.get("n_negatives", 5)
        )
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=config.get("batch_size", 512),
            shuffle=True,
            num_workers=0
        )
        
        # Evaluator
        top_k = config.get("top_k", [10, 20])
        self.evaluator = Evaluator(top_k=top_k)
        
        # Training state
        self.best_val_score = 0.0
        self.patience_counter = 0
        self.early_stopping_patience = config.get("early_stopping_patience", 5)
    
    def train_epoch(self, graph_data) -> float:
        """
        Train for one epoch
        
        Args:
            graph_data: HeteroData graph
            
        Returns:
            Average loss
        """
        self.model.train()
        total_loss = 0.0
        n_batches = 0
        
        # Get embeddings once per epoch
        recipe_text_embeddings = None
        if self.model.use_text_features and "recipes" in self.train_data:
            # Encode recipe texts if available
            recipes = self.train_data["recipes"]
            recipe_texts = {}
            if "combined_text" in recipes.columns:
                for _, row in recipes.iterrows():
                    recipe_idx = row.get("recipe_idx", row.name)
                    text = row.get("combined_text", "")
                    recipe_texts[recipe_idx] = text
            
            if recipe_texts:
                recipe_text_embeddings = self.model.encode_text_features(
                    recipe_texts, self.device
                )
        
        # Forward pass on graph
        embeddings = self.model(graph_data, recipe_text_embeddings)
        
        # Training loop
        for batch in tqdm(self.train_loader, desc="Training"):
            user_indices = batch["user_idx"].to(self.device)
            recipe_indices = batch["recipe_idx"].to(self.device)
            labels = batch["label"].float().to(self.device)
            
            # Get predictions
            user_emb = embeddings["user_embeddings"][user_indices]
            recipe_emb = embeddings["recipe_embeddings"][recipe_indices]
            
            # Compute scores
            scores = (user_emb * recipe_emb).sum(dim=1)
            
            # Compute loss
            loss = self.criterion(scores, labels)
            
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            n_batches += 1
        
        return total_loss / n_batches if n_batches > 0 else 0.0
    
    def validate(self, graph_data) -> Dict[str, float]:
        """
        Validate model
        
        Args:
            graph_data: HeteroData graph
            
        Returns:
            Validation metrics
        """
        # Simple validation on a subset
        val_interactions = self.val_data["val"]
        
        # Sample users for validation
        val_users = val_interactions["user_idx"].unique()[:100]
        
        val_loss = 0.0
        n_samples = 0
        
        self.model.eval()
        with torch.no_grad():
            embeddings = self.model(graph_data)
            
            for user_idx in val_users:
                user_val = val_interactions[val_interactions["user_idx"] == user_idx]
                
                if len(user_val) == 0:
                    continue
                
                user_indices = torch.tensor([user_idx], device=self.device)
                recipe_indices = torch.tensor(
                    user_val["recipe_idx"].values,
                    device=self.device
                )
                
                user_emb = embeddings["user_embeddings"][user_indices]
                recipe_emb = embeddings["recipe_embeddings"][recipe_indices]
                
                scores = (user_emb * recipe_emb).sum(dim=1)
                labels = torch.ones(len(scores), device=self.device)
                
                loss = self.criterion(scores, labels)
                val_loss += loss.item()
                n_samples += 1
        
        return {
            "val_loss": val_loss / n_samples if n_samples > 0 else float('inf')
        }
    
    def train(
        self,
        graph_data,
        save_path: Optional[Path] = None
    ) -> Dict[str, list]:
        """
        Full training loop
        
        Args:
            graph_data: HeteroData graph
            save_path: Path to save checkpoints
            
        Returns:
            Training history
        """
        history = {
            "train_loss": [],
            "val_loss": []
        }
        
        num_epochs = self.config.get("num_epochs", 50)
        
        for epoch in range(num_epochs):
            logger.info(f"Epoch {epoch + 1}/{num_epochs}")
            
            # Train
            train_loss = self.train_epoch(graph_data)
            history["train_loss"].append(train_loss)
            
            # Validate
            val_metrics = self.validate(graph_data)
            val_loss = val_metrics["val_loss"]
            history["val_loss"].append(val_loss)
            
            # Update learning rate scheduler
            if self.scheduler is not None:
                self.scheduler.step(val_loss)
            
            logger.info(f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            if self.scheduler is not None:
                logger.info(f"Learning Rate: {self.optimizer.param_groups[0]['lr']:.6f}")
            
            # Early stopping
            if val_loss < self.best_val_score:
                self.best_val_score = val_loss
                self.patience_counter = 0
                
                # Save best model
                if save_path:
                    save_path.mkdir(parents=True, exist_ok=True)
                    torch.save({
                        "epoch": epoch,
                        "model_state_dict": self.model.state_dict(),
                        "optimizer_state_dict": self.optimizer.state_dict(),
                        "val_loss": val_loss,
                    }, save_path / "best_model.pt")
                    
                    logger.info(f"Saved best model (val_loss: {val_loss:.4f})")
            else:
                self.patience_counter += 1
                if self.patience_counter >= self.early_stopping_patience:
                    logger.info("Early stopping triggered")
                    break
        
        return history

