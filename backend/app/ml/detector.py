"""
Unified Anomaly Detector - Ensemble of Isolation Forest and Autoencoder.
"""

import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.ml.feature_extractor import FeatureExtractor, feature_extractor
from app.ml.isolation_forest import IsolationForestDetector
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from app.ml.autoencoder import AutoencoderDetector
    AUTOENCODER_AVAILABLE = True
except ImportError:
    AUTOENCODER_AVAILABLE = False
    logger.warning("PyTorch not available, Autoencoder disabled")


class AnomalyDetector:
    """Unified anomaly detector combining multiple models."""
    
    def __init__(self, use_ensemble: bool = True):
        self.use_ensemble = use_ensemble and AUTOENCODER_AVAILABLE
        self.feature_extractor = feature_extractor
        
        self.isolation_forest: Optional[IsolationForestDetector] = None
        self.autoencoder: Optional[AutoencoderDetector] = None
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models."""
        try:
            self.isolation_forest = IsolationForestDetector(
                contamination=0.1,
                n_estimators=100
            )
        except Exception as e:
            logger.error(f"Failed to initialize Isolation Forest: {e}")
        
        if self.use_ensemble:
            try:
                self.autoencoder = AutoencoderDetector(
                    input_dim=len(FeatureExtractor.FEATURE_NAMES),
                    encoding_dim=8,
                    epochs=100
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Autoencoder: {e}")
                self.use_ensemble = False
    
    def extract_features(
        self,
        scan_results: List[Dict],
        activities: List[Dict],
        device_info: Dict
    ) -> np.ndarray:
        """Extract features for a device."""
        return self.feature_extractor.extract_features(
            scan_results, activities, device_info
        )
    
    def train(
        self,
        devices_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Train all models on device data.
        
        Args:
            devices_data: List of dicts with 'scan_results', 'activities', 'device_info'
            
        Returns:
            Training results
        """
        logger.info(f"Training anomaly detector with {len(devices_data)} devices")
        
        feature_matrix = []
        for device_data in devices_data:
            features = self.extract_features(
                device_data.get('scan_results', []),
                device_data.get('activities', []),
                device_data.get('device_info', {})
            )
            feature_matrix.append(features)
        
        X = np.array(feature_matrix)
        
        if len(X) < settings.MIN_TRAINING_SAMPLES:
            return {
                "status": "insufficient_data",
                "samples": len(X),
                "required": settings.MIN_TRAINING_SAMPLES
            }
        
        self.feature_extractor.fit_normalizer(X)
        
        results = {"status": "success", "models": {}}
        
        if self.isolation_forest:
            try:
                if_results = self.isolation_forest.train(X)
                results["models"]["isolation_forest"] = if_results
            except Exception as e:
                logger.error(f"Isolation Forest training failed: {e}")
                results["models"]["isolation_forest"] = {"error": str(e)}
        
        if self.use_ensemble and self.autoencoder:
            try:
                ae_results = self.autoencoder.train(X)
                results["models"]["autoencoder"] = ae_results
            except Exception as e:
                logger.error(f"Autoencoder training failed: {e}")
                results["models"]["autoencoder"] = {"error": str(e)}
        
        results["trained_at"] = datetime.utcnow().isoformat()
        results["total_samples"] = len(X)
        
        return results
    
    def predict(
        self,
        scan_results: List[Dict],
        activities: List[Dict],
        device_info: Dict
    ) -> Dict[str, Any]:
        """
        Predict if a device is anomalous.
        
        Args:
            scan_results: Device scan history
            activities: Device activity history
            device_info: Device metadata
            
        Returns:
            Prediction results with ensemble decision
        """
        features = self.extract_features(scan_results, activities, device_info)
        
        results = {
            "device_id": device_info.get("id"),
            "mac_address": device_info.get("mac_address"),
            "predictions": {},
            "ensemble_decision": None,
            "final_score": 0.0,
            "is_anomaly": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        scores = []
        
        if self.isolation_forest and self.isolation_forest.is_trained:
            try:
                if_result = self.isolation_forest.predict_single(features)
                results["predictions"]["isolation_forest"] = if_result
                scores.append(if_result["anomaly_score"])
            except Exception as e:
                logger.error(f"Isolation Forest prediction failed: {e}")
        
        if self.use_ensemble and self.autoencoder and self.autoencoder.is_trained:
            try:
                ae_result = self.autoencoder.predict_single(features)
                results["predictions"]["autoencoder"] = ae_result
                scores.append(ae_result["anomaly_score"])
            except Exception as e:
                logger.error(f"Autoencoder prediction failed: {e}")
        
        if scores:
            results["final_score"] = float(np.mean(scores))
            results["is_anomaly"] = bool(results["final_score"] >= settings.ANOMALY_THRESHOLD)
            
            if len(scores) > 1:
                results["ensemble_decision"] = "consensus" if all(
                    s >= settings.ANOMALY_THRESHOLD for s in scores
                ) or all(
                    s < settings.ANOMALY_THRESHOLD for s in scores
                ) else "disagreement"
        else:
            results["error"] = "No trained models available"
        
        return results
    
    def is_trained(self) -> bool:
        """Check if any model is trained."""
        if_trained = self.isolation_forest and self.isolation_forest.is_trained
        ae_trained = (
            self.use_ensemble and 
            self.autoencoder and 
            self.autoencoder.is_trained
        )
        return if_trained or ae_trained
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models."""
        return {
            "isolation_forest": {
                "available": self.isolation_forest is not None,
                "trained": self.isolation_forest.is_trained if self.isolation_forest else False
            },
            "autoencoder": {
                "available": self.use_ensemble and self.autoencoder is not None,
                "trained": self.autoencoder.is_trained if self.autoencoder else False
            },
            "ensemble_enabled": self.use_ensemble,
            "anomaly_threshold": settings.ANOMALY_THRESHOLD
        }


anomaly_detector = AnomalyDetector()
