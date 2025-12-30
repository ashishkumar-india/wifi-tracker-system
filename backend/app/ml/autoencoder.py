"""
Autoencoder Anomaly Detector - Deep learning based anomaly detection.
"""

import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import logging

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AutoencoderNetwork(nn.Module):
    """Autoencoder neural network architecture."""
    
    def __init__(self, input_dim: int, encoding_dim: int = 8):
        super().__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, encoding_dim),
            nn.ReLU()
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, input_dim)
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
    
    def encode(self, x):
        return self.encoder(x)


class AutoencoderDetector:
    """Autoencoder based anomaly detector using reconstruction error."""
    
    def __init__(
        self,
        input_dim: int = 15,
        encoding_dim: int = 8,
        threshold_percentile: float = 95,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for AutoencoderDetector")
        
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.threshold_percentile = threshold_percentile
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        
        self.model: Optional[AutoencoderNetwork] = None
        self.threshold: float = 0.0
        self.mean: Optional[np.ndarray] = None
        self.std: Optional[np.ndarray] = None
        self.is_trained = False
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = settings.ML_MODEL_PATH / "autoencoder.pth"
        self.stats_path = settings.ML_MODEL_PATH / "autoencoder_stats.npz"
        
        self._load_model()
    
    def train(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Train the autoencoder model.
        
        Args:
            X: Training feature matrix (n_samples, n_features)
            
        Returns:
            Training results dict
        """
        logger.info(f"Training Autoencoder with {len(X)} samples")
        
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0)
        self.std[self.std == 0] = 1
        
        X_normalized = (X - self.mean) / self.std
        
        self.model = AutoencoderNetwork(X.shape[1], self.encoding_dim).to(self.device)
        
        X_tensor = torch.FloatTensor(X_normalized).to(self.device)
        dataset = TensorDataset(X_tensor, X_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        history = {'loss': []}
        
        for epoch in range(self.epochs):
            self.model.train()
            epoch_loss = 0.0
            
            for batch_x, _ in dataloader:
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_x)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(dataloader)
            history['loss'].append(avg_loss)
            
            if (epoch + 1) % 20 == 0:
                logger.info(f"Epoch {epoch+1}/{self.epochs}, Loss: {avg_loss:.6f}")
        
        self.model.eval()
        with torch.no_grad():
            reconstructions = self.model(X_tensor)
            errors = torch.mean((X_tensor - reconstructions) ** 2, dim=1)
            errors_np = errors.cpu().numpy()
        
        self.threshold = np.percentile(errors_np, self.threshold_percentile)
        self.is_trained = True
        
        self._save_model()
        
        results = {
            "model_type": "autoencoder",
            "samples_trained": len(X),
            "input_dim": X.shape[1],
            "encoding_dim": self.encoding_dim,
            "epochs": self.epochs,
            "final_loss": float(history['loss'][-1]),
            "threshold": float(self.threshold),
            "threshold_percentile": self.threshold_percentile,
            "trained_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Training complete: {results}")
        return results
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies for input samples.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            
        Returns:
            Tuple of (predictions, anomaly_scores)
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        X_normalized = (X - self.mean) / self.std
        X_tensor = torch.FloatTensor(X_normalized).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            reconstructions = self.model(X_tensor)
            errors = torch.mean((X_tensor - reconstructions) ** 2, dim=1)
            errors_np = errors.cpu().numpy()
        
        predictions = np.where(errors_np > self.threshold, -1, 1)
        
        max_error = max(errors_np.max(), self.threshold * 2)
        anomaly_scores = errors_np / max_error
        anomaly_scores = np.clip(anomaly_scores, 0, 1)
        
        return predictions, anomaly_scores
    
    def predict_single(self, features: np.ndarray) -> Dict[str, Any]:
        """Predict anomaly for a single sample."""
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        predictions, scores = self.predict(features)
        
        # Convert numpy types to Python native types for JSON serialization
        is_anomaly = bool(predictions[0] == -1)
        score = float(scores[0])
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": score,
            "reconstruction_error": float(score * self.threshold * 2),
            "threshold": float(self.threshold),
            "model_type": "autoencoder",
            "confidence": float(min(abs(score - 0.5) * 2, 1.0))
        }
    
    def _save_model(self):
        """Save model and stats to disk."""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'input_dim': self.input_dim,
                'encoding_dim': self.encoding_dim,
                'threshold': self.threshold
            }, self.model_path)
            
            np.savez(
                self.stats_path,
                mean=self.mean,
                std=self.std
            )
            
            logger.info(f"Autoencoder saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def _load_model(self):
        """Load model from disk if available."""
        try:
            if self.model_path.exists() and self.stats_path.exists():
                # Use weights_only=False for PyTorch 2.6+ compatibility (safe since we control the model files)
                checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
                
                self.input_dim = checkpoint['input_dim']
                self.encoding_dim = checkpoint['encoding_dim']
                self.threshold = checkpoint['threshold']
                
                self.model = AutoencoderNetwork(
                    self.input_dim, 
                    self.encoding_dim
                ).to(self.device)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.model.eval()
                
                stats = np.load(self.stats_path)
                self.mean = stats['mean']
                self.std = stats['std']
                
                self.is_trained = True
                logger.info("Loaded existing Autoencoder model")
                
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            self.is_trained = False
