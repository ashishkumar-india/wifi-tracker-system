"""
Scan result models for storing network scan data.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ScanType(str, enum.Enum):
    """Type of network scan performed."""
    ARP = "arp"
    ICMP = "icmp"
    FULL = "full"


class ScanStatus(str, enum.Enum):
    """Status of a scan session."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanSession(Base):
    """Model for tracking scan sessions/batches."""
    
    __tablename__ = "scan_sessions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    total_devices_found = Column(Integer, default=0)
    new_devices_found = Column(Integer, default=0)
    scan_type = Column(String(20), default="arp", nullable=False)
    network_range = Column(String(50), nullable=True)
    status = Column(String(20), default="running", nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ScanSession(id={self.id}, status='{self.status}', devices={self.total_devices_found})>"
    
    def to_dict(self):
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_devices_found": self.total_devices_found,
            "new_devices_found": self.new_devices_found,
            "scan_type": self.scan_type,
            "network_range": self.network_range,
            "status": self.status,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds
        }
    
    @property
    def duration_seconds(self) -> float:
        """Calculate scan duration in seconds."""
        if not self.completed_at or not self.started_at:
            if self.started_at:
                return (datetime.utcnow() - self.started_at).total_seconds()
            return 0
        return (self.completed_at - self.started_at).total_seconds()
    
    def mark_completed(self, total_devices: int = 0, new_devices: int = 0):
        """Mark scan session as completed."""
        self.completed_at = datetime.utcnow()
        self.status = "completed"
        self.total_devices_found = total_devices
        self.new_devices_found = new_devices
    
    def mark_failed(self, error: str):
        """Mark scan session as failed."""
        self.completed_at = datetime.utcnow()
        self.status = "failed"
        self.error_message = error


class ScanResult(Base):
    """Model for individual scan results per device."""
    
    __tablename__ = "scan_results"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    rssi = Column(Integer, nullable=True)  # Signal strength in dBm
    scan_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_connected = Column(Boolean, default=True, nullable=False)
    response_time_ms = Column(Float, nullable=True)  # Ping response time
    
    # Relationships
    device = relationship("Device", back_populates="scan_results")
    
    def __repr__(self):
        return f"<ScanResult(id={self.id}, device_id={self.device_id}, ip='{self.ip_address}')>"
    
    def to_dict(self):
        """Convert scan result to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "ip_address": self.ip_address,
            "rssi": self.rssi,
            "scan_timestamp": self.scan_timestamp.isoformat() if self.scan_timestamp else None,
            "is_connected": self.is_connected,
            "response_time_ms": self.response_time_ms
        }
