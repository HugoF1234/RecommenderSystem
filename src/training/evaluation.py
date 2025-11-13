"""
Evaluation Module for Save Eat
Implements NDCG@10, Recall@20, MRR metrics
"""

import torch
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Evaluator:
    """
    Evaluates recommendation models using various metrics
    """
    
    def __init__(self, top_k: List[int] = [10, 20, 50]):
        """
        Initialize evaluator
        
        Args:
            top_k: List of k values for evaluation
        """
        self.top_k = top_k
    
    def dcg(self, scores: np.ndarray) -> float:
        """
        Calculate Discounted Cumulative Gain
        
        Args:
            scores: Relevance scores (sorted by predicted ranking)
            
        Returns:
            DCG score
        """
        if len(scores) == 0:
            return 0.0
        
        scores = np.asarray(scores)
        gains = 2 ** scores - 1
        discounts = np.log2(np.arange(len(scores)) + 2)
        
        return np.sum(gains / discounts)
    
    def ndcg_at_k(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        k: int
    ) -> float:
        """
        Calculate NDCG@k
        
        Args:
            predictions: Predicted scores for all items
            ground_truth: Ground truth relevance scores (binary or ratings)
            k: Top k items to consider
            
        Returns:
            NDCG@k score
        """
        # Get top-k predicted items
        top_k_indices = np.argsort(predictions)[::-1][:k]
        
        # Get relevance scores for top-k
        top_k_relevance = ground_truth[top_k_indices]
        
        # Calculate DCG
        dcg = self.dcg(top_k_relevance)
        
        # Calculate ideal DCG (sorted by ground truth)
        ideal_relevance = np.sort(ground_truth)[::-1][:k]
        idcg = self.dcg(ideal_relevance)
        
        # NDCG
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def recall_at_k(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        k: int
    ) -> float:
        """
        Calculate Recall@k
        
        Args:
            predictions: Predicted scores for all items
            ground_truth: Ground truth relevance (binary)
            k: Top k items to consider
            
        Returns:
            Recall@k score
        """
        # Get top-k predicted items
        top_k_indices = np.argsort(predictions)[::-1][:k]
        
        # Count relevant items in top-k
        relevant_in_top_k = np.sum(ground_truth[top_k_indices] > 0)
        
        # Total relevant items
        total_relevant = np.sum(ground_truth > 0)
        
        if total_relevant == 0:
            return 0.0
        
        return relevant_in_top_k / total_relevant
    
    def mrr(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray
    ) -> float:
        """
        Calculate Mean Reciprocal Rank
        
        Args:
            predictions: Predicted scores for all items
            ground_truth: Ground truth relevance (binary)
            
        Returns:
            MRR score
        """
        # Sort by predictions
        sorted_indices = np.argsort(predictions)[::-1]
        
        # Find first relevant item
        for rank, idx in enumerate(sorted_indices, start=1):
            if ground_truth[idx] > 0:
                return 1.0 / rank
        
        return 0.0
    
    def evaluate_user(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray
    ) -> Dict[str, float]:
        """
        Evaluate for a single user
        
        Args:
            predictions: Predicted scores for all items
            ground_truth: Ground truth relevance scores
            
        Returns:
            Dictionary of metric scores
        """
        results = {}
        
        # NDCG@k
        for k in self.top_k:
            results[f"ndcg@{k}"] = self.ndcg_at_k(predictions, ground_truth, k)
        
        # Recall@k
        for k in self.top_k:
            results[f"recall@{k}"] = self.recall_at_k(predictions, ground_truth, k)
        
        # MRR
        results["mrr"] = self.mrr(predictions, ground_truth)
        
        return results
    
    def evaluate(
        self,
        model,
        test_data: Dict,
        device: torch.device,
        batch_size: int = 512
    ) -> Dict[str, float]:
        """
        Evaluate model on test set
        
        Args:
            model: Trained model
            test_data: Test data dictionary
            device: Device
            batch_size: Batch size
            
        Returns:
            Dictionary of average metric scores
        """
        model.eval()
        
        # Get test interactions
        test_interactions = test_data["test"]
        users = test_interactions["user_idx"].unique()
        
        all_results = {f"ndcg@{k}": [] for k in self.top_k}
        all_results.update({f"recall@{k}": [] for k in self.top_k})
        all_results["mrr"] = []
        
        with torch.no_grad():
            # Process users in batches
            for i in range(0, len(users), batch_size):
                batch_users = users[i:i + batch_size]
                
                for user_idx in batch_users:
                    # Get user's test interactions
                    user_test = test_interactions[test_interactions["user_idx"] == user_idx]
                    
                    if len(user_test) == 0:
                        continue
                    
                    # Get all recipes
                    n_recipes = len(test_data["recipes"])
                    
                    # Get predictions for all recipes
                    user_emb = model.user_embedding(torch.tensor([user_idx], device=device))
                    recipe_embs = model.recipe_embedding.weight
                    
                    # Compute scores
                    scores = torch.matmul(user_emb, recipe_embs.T).squeeze().cpu().numpy()
                    
                    # Create ground truth
                    ground_truth = np.zeros(n_recipes)
                    for _, row in user_test.iterrows():
                        recipe_idx = row["recipe_idx"]
                        rating = row.get("rating", 1.0)
                        ground_truth[recipe_idx] = rating
                    
                    # Evaluate
                    user_results = self.evaluate_user(scores, ground_truth)
                    
                    # Accumulate
                    for metric, value in user_results.items():
                        all_results[metric].append(value)
        
        # Average results
        avg_results = {
            metric: np.mean(values) if values else 0.0
            for metric, values in all_results.items()
        }
        
        return avg_results

