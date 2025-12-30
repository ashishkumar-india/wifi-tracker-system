"""
ML Prediction model for storing anomaly detection results.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ModelType(str, enum.Enum):
    """Type of ML model used."""
    ISOLATION_FOREST = "isolation_forest"
    AUTOENCODER = "autoencoder"
    ENSEMBLE = "ensemble"


class MLPrediction(Base):
    """Model for storing ML anomaly detection predictions."""
    
    __tablename__ = "ml_predictions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    model_type = Column(Enum(ModelType), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, nullable=False, index=True)
    confidence = Column(Float, nullable=True)
    features = Column(JSON, nullable=True)
    prediction_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    device = relationship("Device", back_populates="ml_predictions")
    
    def __repr__(self):
        return f"<MLPrediction(id={self.id}, device_id={self.device_id}, is_anomaly={self.is_anomaly})>"
    
    def to_dict(self):
        """Convert prediction to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "model_type": self.model_type.value,
            "anomaly_score": self.anomaly_score,
            "is_anomaly": self.is_anomaly,
            "confidence": self.confidence,
            "features": self.features,
            "prediction_timestamp": self.prediction_timestamp.isoformat() if self.prediction_timestamp else None
        }
    
    @classmethod
    def create_prediction(
        cls,
        device_id: int,
        model_type: ModelType,
        anomaly_score: float,
        threshold: float = 0.7,
        features: dict = None,
        confidence: float = None
    ):
        """Create a new ML prediction."""
        return cls(
            device_id=device_id,
            model_type=model_type,
            anomaly_score=anomaly_score,
            is_anomaly=anomaly_score >= threshold,
            confidence=confidence,
            features=features
        )
