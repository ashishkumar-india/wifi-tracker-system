"""
Alert model for security notifications.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AlertType(str, enum.Enum):
    """Type of alert."""
    NEW_DEVICE = "new_device"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ANOMALY_DETECTED = "anomaly_detected"
    DEVICE_OFFLINE = "device_offline"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class AlertSeverity(str, enum.Enum):
    """Severity level of alert."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    """Model for security alerts."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="medium", nullable=False, index=True)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False, index=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="alerts")
    acknowledged_by_user = relationship("User", back_populates="acknowledged_alerts", foreign_keys=[acknowledged_by])
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.alert_type}', severity='{self.severity}')>"
    
    def to_dict(self, include_device=False):
        """Convert alert to dictionary."""
        data = {
            "id": self.id,
            "device_id": self.device_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
            "is_acknowledged": self.is_acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }
        
        if include_device and self.device:
            data["device"] = {
                "mac_address": self.device.mac_address,
                "hostname": self.device.hostname,
                "vendor": self.device.vendor
            }
        
        return data
    
    def acknowledge(self, user_id: int):
        """Mark alert as acknowledged."""
        self.is_acknowledged = True
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.utcnow()
    
    @classmethod
    def create_new_device_alert(cls, device_id: int, mac_address: str, vendor: str = None):
        """Create alert for new device discovery."""
        return cls(
            device_id=device_id,
            alert_type="new_device",
            severity="medium",
            message=f"New device detected: {mac_address}" + (f" ({vendor})" if vendor else ""),
            details={"mac_address": mac_address, "vendor": vendor}
        )
    
    @classmethod
    def create_anomaly_alert(cls, device_id: int, score: float, model_type: str, mac_address: str):
        """Create alert for ML anomaly detection."""
        severity = "high" if score > 0.85 else "medium"
        return cls(
            device_id=device_id,
            alert_type="anomaly_detected",
            severity=severity,
            message=f"Anomalous behavior detected for device {mac_address} (score: {score:.2f})",
            details={"anomaly_score": score, "model_type": model_type, "mac_address": mac_address}
        )
    
    @classmethod
    def create_suspicious_activity_alert(cls, device_id: int, reason: str, mac_address: str):
        """Create alert for suspicious activity."""
        return cls(
            device_id=device_id,
            alert_type="suspicious_activity",
            severity="high",
            message=f"Suspicious activity for device {mac_address}: {reason}",
            details={"reason": reason, "mac_address": mac_address}
        )
    
    @classmethod
    def create_device_offline_alert(cls, device_id: int, mac_address: str, last_seen: datetime):
        """Create alert for trusted device going offline."""
        return cls(
            device_id=device_id,
            alert_type="device_offline",
            severity="low",
            message=f"Trusted device {mac_address} is offline",
            details={"mac_address": mac_address, "last_seen": last_seen.isoformat() if last_seen else None}
        )
