"""
Device model for tracked network devices.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Device(Base):
    """Model for network devices discovered during scans."""
    
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mac_address = Column(String(17), unique=True, nullable=False, index=True)
    hostname = Column(String(255), nullable=True)
    vendor = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_trusted = Column(Boolean, default=False, nullable=False, index=True)
    is_suspicious = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    scan_results = relationship("ScanResult", back_populates="device", cascade="all, delete-orphan")
    activities = relationship("DeviceActivity", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device")
    ml_predictions = relationship("MLPrediction", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Device(id={self.id}, mac='{self.mac_address}', hostname='{self.hostname}')>"
    
    def to_dict(self, include_latest_scan=False):
        """Convert device to dictionary."""
        data = {
            "id": self.id,
            "mac_address": self.mac_address,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "device_type": self.device_type,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "is_trusted": self.is_trusted,
            "is_suspicious": self.is_suspicious,
            "notes": self.notes,
        }
        
        if include_latest_scan and self.scan_results:
            latest = max(self.scan_results, key=lambda x: x.scan_timestamp)
            data["latest_scan"] = latest.to_dict()
        
        return data
    
    def update_last_seen(self):
        """Update the last_seen timestamp."""
        self.last_seen = datetime.utcnow()
    
    @property
    def is_online(self) -> bool:
        """Check if device was seen in the last 10 minutes."""
        if not self.last_seen:
            return False
        return (datetime.utcnow() - self.last_seen).total_seconds() < 600
    
    @property 
    def time_since_last_seen(self) -> int:
        """Get seconds since device was last seen."""
        if not self.last_seen:
            return -1
        return int((datetime.utcnow() - self.last_seen).total_seconds())
