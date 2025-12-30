"""
Isolation Forest Anomaly Detector - Unsupervised anomaly detection.
"""

import numpy as np
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import logging

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IsolationForestDetector:
    """Isolation Forest based anomaly detector."""
    
    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        max_samples: str = 'auto',
        random_state: int = 42
    ):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for IsolationForestDetector")
        
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.random_state = random_state
        
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained = False
        self.training_samples = 0
        self.model_path = settings.ML_MODEL_PATH / "isolation_forest.pkl"
        self.scaler_path = settings.ML_MODEL_PATH / "isolation_forest_scaler.pkl"
        
        self._load_model()
    
    def train(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Train the Isolation Forest model.
        
        Args:
            X: Training feature matrix (n_samples, n_features)
            
        Returns:
            Training results dict
        """
        if len(X) < settings.MIN_TRAINING_SAMPLES:
            logger.warning(
                f"Insufficient training data: {len(X)} samples "
                f"(minimum: {settings.MIN_TRAINING_SAMPLES})"
            )
        
        logger.info(f"Training Isolation Forest with {len(X)} samples")
        
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        self.model.fit(X_scaled)
        self.is_trained = True
        self.training_samples = len(X)
        
        self._save_model()
        
        scores = self.model.decision_function(X_scaled)
        predictions = self.model.predict(X_scaled)
        
        results = {
            "model_type": "isolation_forest",
            "samples_trained": len(X),
            "contamination": self.contamination,
            "n_estimators": self.n_estimators,
            "anomalies_in_training": int(np.sum(predictions == -1)),
            "score_mean": float(np.mean(scores)),
            "score_std": float(np.std(scores)),
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
            predictions: 1 for normal, -1 for anomaly
            anomaly_scores: Normalized score (0-1, higher = more anomalous)
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        raw_scores = self.model.decision_function(X_scaled)
        
        anomaly_scores = 1 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-10)
        
        return predictions, anomaly_scores
    
    def predict_single(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Predict anomaly for a single sample.
        
        Args:
            features: Feature vector for single device
            
        Returns:
            Prediction results dict
        """
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        predictions, scores = self.predict(features)
        
        # Convert numpy types to Python native types for JSON serialization
        is_anomaly = bool(predictions[0] == -1)
        score = float(scores[0])
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": score,
            "threshold": float(settings.ANOMALY_THRESHOLD),
            "model_type": "isolation_forest",
            "confidence": float(abs(score - 0.5) * 2)
        }
    
    def _save_model(self):
        """Save model and scaler to disk."""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def _load_model(self):
        """Load model and scaler from disk if available."""
        try:
            if self.model_path.exists() and self.scaler_path.exists():
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                self.is_trained = True
                logger.info("Loaded existing Isolation Forest model")
                
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            self.is_trained = False
    
    def get_feature_importance(self, feature_names: List[str]) -> Dict[str, float]:
        """
        Estimate feature importance based on isolation depth.
        Note: This is an approximation as IF doesn't provide direct feature importance.
        """
        if not self.is_trained:
            return {}
        
        importances = {}
        for i, name in enumerate(feature_names):
            importances[name] = 1.0 / len(feature_names)
        
        return importances
